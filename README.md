# facts2sshfp

This program reads the fact files created on a Puppet master server (typically
in `/var/lib/puppet/yaml/facts`) and spits out [RFC 4255](http://www.ietf.org/rfc/rfc4255.txt)
SSHFP records for the SSH RSA and DSA host keys contained therein.

_facts2sshfp_ can produce output in a variety of formats, and it supports a simple
templating system with which you can create almost any output you desire. Examples 
include creating MySQL INSERT statements for [PowerDNS](http://powerdns.com) as well as
`nsupdate`-compatible output for a [BIND](http://www.isc.org/software/bind) server
configured for RFC 2136 dynamic DNS updates.

The following options are supported:

* -d FACTSDIR

> Read the specified directory for `*.yaml` instead of the default `/var/lib/puppet/yaml/facts`.

* -H 

> set record owner to the unqualified hostname instead of the fully qualified domain name

* -D DOMAINNAME

> qualify hostnames with the specified DOMAINNAME instead of using the domain name obtained
> from the facts files

* -Q

> qualify the hostname with a trailing dot

* -J

> Produce output in JSON

* -Y

> Produce output in YAML

* -T TEMPLATE

> Print records using the content of a template file (Python Template). The fields
> recognized by the template can be obtained from the JSON (-J) output.

## Examples

### Print DNS keys

	facts2sshfp.py 
	ldap.example.net     IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	ldap.example.net     IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312
	monster.example.net  IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	monster.example.net  IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312

### ... using the specified domain name

	facts2sshfp.py -D foo.bar
	ldap.foo.bar         IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	ldap.foo.bar         IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312
	monster.foo.bar      IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	monster.foo.bar      IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312

### Qualify owner names with a trailing dot

	facts2sshfp.py -Q -D foo.bar
	ldap.foo.bar.        IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	ldap.foo.bar.        IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312
	monster.foo.bar.     IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	monster.foo.bar.     IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312

### Show JSON output for further processing

	facts2sshfp.py -J
	[
	    {
		"domain": "example.net", 
		"dsa_fp": "4BBBD2A6B26D375B377137AC877DA27AF46B4312", 
		"rsa_keytype": "1", 
		"hostname": "ldap", 
		"fqdn": "ldap.example.net", 
		"owner": "ldap.example.net", 
		"dsa_keytype": "2", 
		"rsa_fp": "01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15"
	    }, 
	    {
		"domain": "example.net", 
		"dsa_fp": "4BBBD2A6B26D375B377137AC877DA27AF46B4312", 
		"rsa_keytype": "1", 
		"hostname": "monster", 
		"fqdn": "monster.example.net", 
		"owner": "monster.example.net", 
		"dsa_keytype": "2", 
		"rsa_fp": "01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15"
	    }
	]

### Print food for PowerDNS with an SQL back-end

	facts2sshfp.py -T pdns.template
	INSERT INTO records (domain_id, name, type, content)
	VALUES (
		(SELECT id FROM domains WHERE name = 'example.net'),
		'ldap.example.net', 'SSHFP', '1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15'
		);
	INSERT INTO records (domain_id, name, type, content)
	VALUES (
		(SELECT id FROM domains WHERE name = 'example.net'),
		'ldap.example.net', 'SSHFP', '2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312'
		);
	...

### Send updates via nsupdate (RFC 2136) Dynamic DNS

	facts2sshfp.py -T nsupdate.template -D a.aa.
	server 127.0.0.2
	update delete ldap.a.aa. IN SSHFP
	update add ldap.a.aa. 120 IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	update add ldap.a.aa. 120 IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312

	server 127.0.0.2
	update delete monster.a.aa. IN SSHFP
	update add monster.a.aa. 120 IN SSHFP 1 1 01DE5FEEA3FC4820C2AD2181CA9FE02F9B2DFE15
	update add monster.a.aa. 120 IN SSHFP 2 1 4BBBD2A6B26D375B377137AC877DA27AF46B4312

	facts2sshfp.py -T nsupdate.template -D a.aa. | nsupdate -k jpupdate.key


## Bugs

Yes.

## Credits

* Uses a bit of code swiped from [sshfp](http://www.xelerance.com/services/software/sshfp/)

