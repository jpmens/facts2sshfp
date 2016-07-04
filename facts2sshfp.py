#!/usr/bin/env python
#(@)facts2sshfp.py (C) February 2012, by Jan-Piet Mens <jpmens@gmail.com>
# with inspiration from Pieter Lexis
#
# Slurp through the YAML fact files collected on a Puppet master,
# extract the SSH RSA/DSA public keys and produce SSHFP records for DNS.
# See also: http://jpmens.net/2011/07/21/it-s-a-fact-in-puppet/
#      and: http://jpmens.net/2012/02/01/on-collecting-ssh-host-keys-for-sshfp-dns-records/
#
# This program contains create_sshfp, which I swiped from Paul Wouter's SSHFP at
# http://www.xelerance.com/services/software/sshfp/. I have removed the hostname
# magic, because not needed here, as we know the fqdn (hopefully)


import glob
import sys, re
import yaml
import json
import base64
try:
    import hashlib
    digest = hashlib.sha1
except ImportError:
    import sha
    digest = sha.new
import string
from string import Template
import optparse
from getpass import getpass

factsdir = '/var/lib/puppet/yaml/facts'

def create_sshfp(hostname, keytype, keyblob):
    """Creates an SSH fingerprint"""

    if keytype == "ssh-rsa":
        keytype = "1"
    elif keytype == "ssh-dss":
        keytype = "2"
    elif keytype == "ssh-ecdsa":
        keytype = "3"
    else:
        return ""
    try:
        rawkey = base64.b64decode(keyblob)
    except TypeError:
        print >> sys.stderr, "FAILED on hostname "+hostname+" with keyblob "+keyblob
        return "ERROR"

    fpsha1 = digest(rawkey).hexdigest().upper()

    # return hostname + " IN SSHFP " + keytype + " 1 " + fpsha1
    return {
        "keytype"   : keytype,
        "fpsha1"    : fpsha1
    }

def facts_to_dict(filename):
    """
    Return dict from YAML contained in filename, having removed the
    fugly Ruby constructs added by Puppet.
    (e.g. --- !ruby/object:Puppet::Node::Facts) which no YAML
    """

    searchregex = "!ruby.*\s?"
    cregex = re.compile(searchregex)

    # "--- !ruby/sym _timestamp": Thu Jan 12 12:25:02 +0100 2012
    # !ruby/sym _timestamp: Tue Oct 04 07:56:54 +0200 2011
    rubyre = '"?(--- )?!ruby/sym ([^"]+)"?:\s+(.*)$'
    nrub = re.compile(rubyre)


    stream = ''
    for line in open(filename, 'r'):

        # Pieter reports his fact files contain e.g. ec2_userdata with binary blobs in them
        # Remove all that binary stuff....

        line = filter(lambda x: x in string.printable, line)
        if nrub.search(line):
            line = nrub.sub(r'\2: \3', line)
        if cregex.search(line):
            line = cregex.sub("\n", line)
        stream = stream + line

    yml = yaml.load(stream)
    return yml['values']

if __name__ == '__main__':

    naming = 'fqdn'
    domainname = ''
    template = ''
    keylist = []

    parser = optparse.OptionParser()
    parser.add_option('-d', '--directory', dest='factsdir', help='Directory containing facts')
    parser.add_option('-H', '--hostname',  dest='usehost', default=False, help='Use hostname i/o fqdn',
        action='store_true')
    parser.add_option('-D', '--domainname', dest='domainname', help='Append domain')
    parser.add_option('-F', '--foreman-url', dest='foremanurl', help='Foreman URL')
    parser.add_option('-u', '--foreman-username', dest='foremanusername', help='Foreman username')
    parser.add_option('-p', '--foreman-password', dest='foremanpassword', help='Foreman password')
    parser.add_option('-Q', '--qualify', dest='qualify', default=False, help='Qualify hostname with dot', action='store_true')
    parser.add_option('-J', '--json', dest='jsonprint', default=False, help='Print JSON', action='store_true')
    parser.add_option('-Y', '--yaml', dest='yamlprint', default=False, help='Print YAML', action='store_true')
    parser.add_option('-T', '--template', dest='templatename', help='Print using template file')
    parser.add_option('-j', '--jinja2-template', dest='j2templatename', help='Print using Jinja2 template file')


    (opts, args) = parser.parse_args()

    if opts.factsdir:
        factsdir =  opts.factsdir
    if opts.usehost:
        naming = 'hostname'
    if opts.domainname:
        domainname = opts.domainname
    if opts.templatename:
        template = open(opts.templatename, 'r').read()

    if not opts.foremanurl:
        for filename in glob.glob(factsdir + "/*.yaml"):
            facts = facts_to_dict(filename)

            item = {}
            rsa = create_sshfp(facts[naming], 'ssh-rsa', facts['sshrsakey'])
            dsa = create_sshfp(facts[naming], 'ssh-dss', facts['sshdsakey'])
            ecdsa = None
            if 'sshecdsakey' in facts:
                ecdsa = create_sshfp(facts[naming], 'ssh-ecdsa', facts['sshecdsakey'])

            item['hostname']        = facts['hostname']
            item['fqdn']            = facts['fqdn']
            if domainname != '':
                item['domain']          = domainname
            else:
                item['domain']          = facts['domain']

            if naming == 'hostname':
                owner = item['hostname']
            else:
                owner = item['hostname'] + '.' + item['domain']
            if opts.qualify == True:
                owner = owner + '.'
            item['owner']           = owner

            item['rsa_fp']          = rsa['fpsha1']
            item['rsa_keytype']     = rsa['keytype']
            item['dsa_fp']          = dsa['fpsha1']
            item['dsa_keytype']     = dsa['keytype']
            if ecdsa:
                item['ecdsa_fp']          = ecdsa['fpsha1']
                item['ecdsa_keytype']     = ecdsa['keytype']


            keylist.append(item)
    else:
        from foreman.client import Foreman
        if not opts.foremanpassword:
            password = getpass()
        f = Foreman(opts.foremanurl, (opts.foremanusername, password))

        key_map = {
                    'dsa': ('sshdsakey', 'ssh-dss'),
                    'rsa': ('sshrsakey', 'ssh-rsa'),
                    'ecdsa': ('sshecdsakey', 'ssh-ecdsa'),
                    'ed25519': ('sshed25519key', 'ssh-ed25519'),
                }
        for keytype in key_map:
            fact_name, ssh_key_type = key_map[keytype]
            facts = f.fact_values.index(999, search="name=%s" % fact_name)
            for host in facts:
                key = create_sshfp(host, ssh_key_type, facts[host][fact_name])
                item = {}
                item['%s_fp' % keytype] = key['fpsha1']
                item['%s_keytype' % keytype] = key['keytype']
                item['owner'] = host
                keylist.append(item)

    if opts.jsonprint == True:
        print json.dumps(keylist, indent=4)
    elif opts.j2templatename:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(opts.j2templatename)
        print template.render(keylist=keylist)
    elif opts.yamlprint == True:
        print yaml.dump(keylist, default_flow_style=False, explicit_start=True)
    elif opts.templatename:
        for item in keylist:
            s = Template(template)
            print s.substitute(item)
    else:
        for item in keylist:
            print "%-20s IN SSHFP %s 1 %s" % (item['owner'], item['rsa_keytype'], item['rsa_fp'])
            print "%-20s IN SSHFP %s 1 %s" % (item['owner'], item['dsa_keytype'], item['dsa_fp'])
            if 'ecdsa_keytype' in item:
                print "%-20s IN SSHFP %s 1 %s" % (item['owner'], item['ecdsa_keytype'], item['ecdsa_fp'])

