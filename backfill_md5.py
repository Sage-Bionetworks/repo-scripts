#!/usr/bin/python

import boto
import os

conn = boto.connect_s3()
bucket = conn.get_bucket('proddata.sagebase.org')

output = open('output', 'w+')
input_file = raw_input('Input File: ')
lines = open(input_file).read().splitlines()
total = len(lines)
count = 0
for line in lines:
    count = count + 1
    print 'Processing', count, 'of', total
    splits = line.split("\t")
    file_size = long(splits[1])
    # Download the file from S3
    key = bucket.get_key(splits[4].replace('\"', ''))
    if key is None:
        print 'ERROR: Failed to retrieve', splits[0], 'skipped'
        continue
    key_size = key.size
    if key_size <> file_size:
        print 'ERROR: Size does not match in S3 and RDS.', splits[0], 'skipped.'
        continue
    file_name = 'tempfile'
    temp_file = open(file_name, 'w+')
    key.get_file(temp_file)
    key.close()
    temp_file.close()
    # Verify file size
    downloaded_size = os.path.getsize(file_name)
    if key_size <> downloaded_size:
        print 'ERROR: Size of the downloaded file does not match.', splits[0], 'skipped.'
        continue
    # Compute md5
    temp_file = open(file_name, 'r')
    md5 = key.compute_md5(temp_file)
    temp_file.close()
    os.remove(file_name)
    # Write output
    line = line + '\t' + md5[0] + '\r\n'
    output.write(line)

output.close()

