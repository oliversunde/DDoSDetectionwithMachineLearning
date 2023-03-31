#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_folder>"
    exit 1
fi

output_folder=$1
mkdir -p $output_folder

for i in {1..24}; do
    mnexec -a h$i tcpdump -i h$i-eth0 -w $output_folder/h$i.pcap &
done

#remember to give it exec rights
#chmod +x start_tcpdump.sh
#and then start it with, edit output folder in the script and when running the shell
#./start_tcpdump.sh <output_folder>
