#!/usr/bin/python

import boto
import os

conn = boto.connect_s3()
bucket = conn.get_bucket('proddata.sagebase.org')

# Input file are rows selected from the MySQL db where MD5 is missing
input_file = raw_input('Input File: ')
lines = open(input_file).read().splitlines()
total = len(lines)
count = 0
# Output file will have the computed MD5
output_file = open('output', 'w+')
for line in lines:
    count = count + 1
    print('Processing', count, 'of', total)
    splits = line.split("\t")
    file_id = splits[0]
    file_size = long(splits[1])
    # Some key values are double quoted. The double quotes must be removed.
    file_key = splits[4].replace('\"', '')
    # Verify size. Make sure S3 has the complete file.
    key = bucket.get_key(file_key)
    if key is None:
        print('ERROR: Failed to retrieve.', file_id, 'skipped.')
        continue
    key_size = key.size
    if key_size != file_size:
        print('ERROR: Size does not match in S3 and RDS.', file_id, 'skipped.')
        continue
    # Download the file from S3
    file_name = 'tempfile'
    temp_file = open(file_name, 'w+')
    key.get_file(temp_file)
    key.close()
    temp_file.close() # Must close file before getting the file size
    # Verify the downloaded file size
    downloaded_size = os.path.getsize(file_name)
    if key_size != downloaded_size:
        print('ERROR: Size of the downloaded file does not match.', file_id, 'skipped.')
        continue
    # Compute md5
    temp_file = open(file_name, 'r')
    md5 = key.compute_md5(temp_file)
    temp_file.close()
    os.remove(file_name)
    # Write output
    line = line + '\t' + md5[0] + '\r\n'
    output_file.write(line)

output_file.close()

