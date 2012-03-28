#!/usr/bin/env python
#coding: utf-8

__author__="hechao"
__date__ ="$2011-12-20 16:32:44$"

import re
import os
import sys
import hashlib
import commands
from subprocess import Popen,PIPE
from globals import *
from dbuscall import init_dbus

def get_output(cmd):
    status, output = commands.getstatusoutput(cmd)
    if status: raise
    return output

def record_sign():
    try:
	import lshw
	degree = lshw.record_sign()
	return degree
    except:
	return "C"

def readfile(name):
    try:
	with open(name, 'r') as fp:
            return fp.read()
    except:
        return 'N/A'

def host_name():
    host_name.please_refresh_me = True
    try:
	return get_output('hostname')
    except:
	return ""

def kernel():
    ret = []
    try: ret.append(get_output('uname -r'))
    except: pass

    try: ret.append(get_output('uname -m'))
    except: pass
    return ret

def xorg():
    try:
        for line in get_output('Xorg -version').split('\n'):
            if line.startswith('X.Org X Server'):
                return line.strip()
    except:
        return ""

def uptime():
    ret = {}
    try:
        with open('/proc/uptime') as fp:
            string = fp.read().split('.')[0]
        seconds = int(string)
        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        minutes %= 60
        hours %= 24
        if days:
	    ret["day"] = str(days)
        if hours:
	    ret["hour"] = str(hours)
        if minutes:
	    ret["minute"] = str(minutes)

    except:
	print >> sys.stderr, 'uptime failed'

    return ret

def install_time():
    try:
        import time
        with open('/etc/install_date') as fp:
            date = fp.read().strip('\n')
            date = time.localtime(float(date))
        return time.strftime("%Y-%m-%d %H:%M:%S %A", date)
    except:
        return ""

def user():
    try:
        import os
        string = '%s (UID: %s, GID: %s)' % (os.environ['USER'], os.getuid(), os.getgid())
        return string
    except:
        return ""

def opengl():
    ret = []
    try:
        direct_render = vendor_version = renderer = ''
        f = get_output('glxinfo')
        for line in f.split('\n'):
            v = line.split(':')
            if v[0] == 'direct rendering':  direct_render = v[1].strip()
	    if v[0] == 'OpenGL renderer string': renderer = v[1].strip()
            if v[0] == 'OpenGL version string': vendor_version = v[1].strip()
        ret.append(direct_render)
	ret.append(renderer)
	ret.append(vendor_version)

    except:
        print >> sys.stderr, 'Command failed: glxinfo'
    return ret

def os_version():
    try:
        import platform
        name, version, code = platform.dist()
        return version + " " + code
    except:
        return ""

def udisks(dev):
    ret = {}
    try:
	info = get_output('udisks --show-info %s' % dev)

	boot = re.findall("detected at:\s*(.*)", info)
	if boot:
	    ret["boot"] = boot[0].strip()

	wwn = re.findall("WWN:\s*(.*)", info)
	if wwn:
	    ret["wwn"] = wwn[0].strip()

	rota = re.findall("rotational media:.*at (.*)", info)
	if rota:
	    ret["rota"] = rota[0].strip()

	state = re.findall("overall assessment:\s*(.*)", info)
	if state:
	    ret["state"] = state[0].strip()

	sumtime = re.findall("power-on-hours.*(n/a|good)\s*(.*)Old-age", info)
	if sumtime:
	    ret["sumtime"] = sumtime[0][1].strip()

	sumnub = re.findall("power-cycle-count.*(n/a|good)\s*(\d*)", info)
	if sumnub:
	    ret["sumnub"] = sumnub[0][1]

	temp = re.findall("temperature-celsius-2.*(n/a|good)\s*(\d*)", info)
	if temp:
	    temp = temp[0][1]
	    ret["temp"] = temp + record_sign()

	unsect = re.findall("offline-uncorrectable.*(n/a|good)\s*(\d*)", info)
	if unsect:
	    ret["unsect"] = unsect[0][1]

    except:
        print >> sys.stderr, 'Command failed: udisks'
    return ret

def sensors():
    #info = get_output("lsmod")
    #coretemp = re.findall("coretemp",info)
    try:
        get_output("lsmod | grep -w coretemp")
    except:
        iface = init_dbus()
	iface.modprobe()
	iface.quit_loop()
    try:
	import lshw
	temp = lshw.sensors()
	return temp
    except:
	return ""

def get_monitor():
    ret = {}
    try:
	info = readfile("/var/log/Xorg.0.log")
        tmp = re.findall("Monitor name: \s*(\w*)\s*(\w*)", info)
        #tmp = re.findall("Monitor name: \s*(.*)", info)
        if tmp:
            if tmp[0][1]:
                ret["vendor"] = tmp[0][0]
                ret["product"] = tmp[0][0] + " " + tmp[0][1]
            else:ret["product"] = tmp[0][0]
        
        tmp = re.findall("Manufacturer:\s*(\w*)\s*Model:\s*(\w*)", info)
        if tmp:
            if not ret.get("product"):
                ret["product"] = tmp[0][0] + " " + tmp[0][1]
            if not ret.get("vendor"):
                ret["vendor"] = tmp[0][0]

	tmp = re.findall("Year:\s*(\w*)\s*Week:\s*(\w*)", info)
      
	if tmp:
	    ret["year"] = tmp[0][0]
	    ret["week"] = tmp[0][1]

	tmp = re.findall("EDID Version: (\S*)", info)
	if tmp:
	    ret["version"] = tmp[0]

	tmp = re.findall("Max Image Size \[(\w*)\]: horiz.: (\w*)\s*vert.: (\w*)", info)
	if tmp:
	    ret["size"] = tmp[0][1] + tmp[0][0] + "x" + tmp[0][2] + tmp[0][0]

	tmp = re.findall("Gamma: (\S*)", info)
	if tmp:
	    ret["gamma"] = tmp[0]

	h = re.findall("h_active: (\d*)", info)
	v = re.findall("v_active: (\d*)", info)
	if h and v:
	    ret["maxmode"] = h[0] + "x" + v[0]

	tmp = re.findall("EDID for output (\D*)", info)
	if tmp:
	    ret["support output"] = tmp

	tmp = re.findall("Output (\D*).* connected", info)
	if tmp:
	    ret["output"] = tmp[0]

	tmp = re.findall("Output \w* using initial mode (\w*)", info)
	if tmp:
	    ret["mode"] = tmp[0]

	tmp = re.findall("Integrated Graphics Chipset: (.*)", info)
	if tmp:
	    ret["chip"] = tmp[0]

    except:
	print >> sys.stderr, 'Read Xorg log failed!'

    return ret

def cpuinfo():
    info = readfile("/proc/cpuinfo")
    return str(len(re.findall("processor\s*:\s*(.*)", info)))

def environ():
    env = dict(os.environ)
    return repr(env)

def get_status(name):
    ret = "*"
    try:
        info = get_output("yget --status %s" %name)
        status = re.findall("Status:\s*(.*)", info)
        ret = status[0]
        return ret
    except:
        return ret

def open_conf():
    '''open config file'''
    try:
        with open(CONFIG, "r") as fp:
            data = fp.read()

        for line in data.split('\n'):
            path = re.match("YPPATH_URI=\"(.*)\"",line)
            if path:
                return path.group(1)
    except:
        return "http://pkg.ylmf.com/packages"

def cmd_down():
    '''cmd down'''
    url = open_conf()

    env = eval(environ())
    if not env.get('DISPLAY'):
        cmd = "curl --connect-timeout 10 --retry 2 -4 %s/driver.xml.tar.bz2 -o %s/driver.xml.tar.bz2" %(url, TARGET_DIR)
        (status, output) = commands.getstatusoutput(cmd)
    else:
        cmd = "%s/terminal.py curl --connect-timeout 10 --retry 2 -4 %s/driver.xml.tar.bz2 -o %s/driver.xml.tar.bz2" %(RUN_DIR, url, TARGET_DIR)
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, env=env)
        status = process.wait()

    if status:
        return C_Errno, "Network connection error, check your network!"
    else:
        return check_file("%s/driver.xml.tar.bz2" %TARGET_DIR, url)

def ui_down():
    '''ui down'''
    url = open_conf()

    cmd = "curl --connect-timeout 10 --retry 2 -4 %s/driver.xml.tar.bz2 -o %s/driver.xml.tar.bz2" %(url, TARGET_DIR)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    status = process.wait()

    if status:
        return C_Errno, "Network connection error, check your network!"
    else:
        return check_file("%s/driver.xml.tar.bz2" %TARGET_DIR, url)

def check_file(tar_file, url):
    '''check file'''
    hash_new = hashlib.sha1()
    with open(tar_file, 'rb') as fp:
        while True:
            data = fp.read()
            if not data:
                break
            hash_new.update(data)
    hash_value = hash_new.hexdigest()

    cmd = "curl --connect-timeout 10 --retry 2 -4 %s/driver.xml.tar.bz2.sha1sum" %url
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    status = process.wait()

    if status:
        return C_Errno, "Network connection error, check your network!"
    else:
        sha1sum = process.stdout.read().split()[0]

    if hash_value == sha1sum:
        os.system("tar -jxf %s -C %s" %(tar_file, TARGET_DIR))
        return 0, "%s/driver.xml" %TARGET_DIR
    else:
        #return P_Errno, "File checksum error!"
        '''test'''
        cmd = "curl --connect-timeout 10 --retry 2 -4 %s/driver.xml -o %s/driver.xml" %(url, TARGET_DIR)
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        return 0, "%s/driver.xml" %TARGET_DIR

