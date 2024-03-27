#!/bin/bash

URL="https://github.com/networktocode/ntc-templates/archive/refs/heads/master.zip"

wget -q $URL
rm -rf netdoc/ntc_templates ntc-templates-master
unzip -qq master.zip
mv ntc-templates-master/ntc_templates/templates netdoc/ntc_templates
rm -rf master.zip ntc-templates-master
