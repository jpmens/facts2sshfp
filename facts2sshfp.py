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
import codecs
import base64
try:
    import hashlib
    digest = hashlib.sha1
except ImportError:
    import sha
    digest = sha.new
import string

factsdir = '/var/lib/puppet/yaml/facts'


def create_sshfp(hostname, keytype, keyblob):
	"""Creates an SSH fingerprint"""

	if keytype == "ssh-rsa":
		keytype = "1"
	else:
		if keytype == "ssh-dss":
			keytype = "2"
		else:
			return ""
	try:
		rawkey = base64.b64decode(keyblob)
	except TypeError:
		print >> sys.stderr, "FAILED on hostname "+hostname+" with keyblob "+keyblob
		return "ERROR"
	fpsha1 = digest(rawkey).hexdigest().upper()

	return hostname + " IN SSHFP " + keytype + " 1 " + fpsha1

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

    for filename in glob.glob(factsdir + "/*.yaml"):
        facts = facts_to_dict(filename)

        r = create_sshfp(facts['fqdn'], 'ssh-rsa', facts['sshrsakey'])
        print(r)    
        r = create_sshfp(facts['fqdn'], 'ssh-dss', facts['sshdsakey'])
        print(r)    
