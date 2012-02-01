# facts2sshfp

This program reads the fact files created on a Puppet master server (typically
in `/var/lib/puppet/yaml/facts`) and spits out [RFC 4255](http://www.ietf.org/rfc/rfc4255.txt)
SSHFP records for the SSH RSA and DSA host keys contained therein.

Hostnames are taken from the `fqdn` fact.

	$ ./facts2sshfp
	foo.example.net IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	foo.example.net IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312
	...
	bar.example.org IN SSHFP 1 1 41DF17ECE294E2530CC754BD3E7AD61054A8D4DF
	bar.example.org IN SSHFP 2 1 EF7891A6419E1673789C29B78D1DADE3E8634247
