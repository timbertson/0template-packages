#!/usr/bin/env python
import logging
import sys, os
import yaml
from optparse import OptionParser
import jinja2
import subprocess
import re

def main():
	p = OptionParser("Usage: %prog input.yml")
	p.add_option('-i', '--input', default='packages.yml', help="(%default)")
	p.add_option('-p', '--prefix', default='build', help="(%default)")
	p.add_option('-t', '--template', default='template.xml', help="(%default)")
	opts, args = p.parse_args()

	logging.basicConfig(level=logging.DEBUG)
	conffile = opts.input
	with open(conffile) as f:
		conf = yaml.load(f.read())
	templatefile = opts.template
	prefix = opts.prefix
	with open(templatefile) as f:
		template = jinja2.Template(f.read())
	process(prefix, conf, template, names=args)

DISTS = {
		'debian': 'Debian',
		'rpm': 'RPM',
		'arch': 'Arch',
		'slack': 'Slack',
		'ports': 'Ports',
		'gentoo': 'Gentoo',
		'cygwin': 'Cygwin',
	}

def to_list(l):
	if not isinstance(l, list):
		l = [l]
	return l

def process(prefix, config, template, names):
	if not os.path.isdir(prefix):
		os.makedirs(prefix)
	files_in_output = set(os.listdir(prefix))
	def file_name(name):
		return os.path.join(prefix, "%s.xml" % (name,))
	generated_files = set([])

	for name, details in config.items():
		if names and (name not in names):
			print "skipping %s..." % (name,)
			continue
		if details is None:
			details = {}
		logging.debug("Processing %s: %r" %(name,details))
		details['name'] = name

		distros = {}
		for dist_key, distro_name in DISTS.items():
			if dist_key in details:
				dist_details = details[dist_key]
				if isinstance(dist_details, str) or isinstance(dist_details, unicode) or isinstance(dist_details, list):
					dist_details = {'package': to_list(dist_details)}
				else:
					# ensure package is a list
					dist_details['package'] = to_list(dist_details['package'])
				dist_details['distro_name'] = distro_name
				distros[dist_key] = dist_details
		if not distros and 'package' not in details:
			details['package'] = name

		if 'package' in details:
			# force list
			details['package'] = to_list(details['package'])

		details['distros'] = distros
		output_filename = file_name(name)
		generated_files.add(output_filename[len(prefix)+1:])
		with open(output_filename, 'w') as output:
			logging.debug("rendering template with values: %r" % (details,))
			contents = template.render(details)
			contents = re.sub('^\s*\n', '', contents, flags=re.MULTILINE)
			output.write(contents)

		# subprocess.check_call(['0publish', '--xmlsign', output_filename])
		logging.info("generated %s" % (output_filename,))

	for unexpected_file in files_in_output.difference(generated_files):
		if unexpected_file.endswith('.gpg'): continue
		logging.warn("Unexpected file in output directory: %s" %(os.path.join(prefix, unexpected_file),))

	print "Generated %s files" %(len(generated_files),)

if __name__ == '__main__':
	sys.exit(main())
