#!/usr/bin/env bash

tempfile=~/test.img

declare -A test_config=(["1K"]="1000" ["64K"]="1000" ["512K"]="1000" ["1M"]="1000" ["1G"]="4")

echo "Disk Speed Test"

for key in "${!test_config[@]}"
    do
        echo ""
        echo ""
        echo "*****Testing $key:${test_config[$key]}*****"
        rm "$tempfile" || true
        cmd="dd if=/dev/zero of=$tempfile bs=$key count=${test_config[$key]}"
        echo "$cmd"
        $cmd
        echo "-------READ TEST------"
        cmd="dd if=$tempfile of=/dev/zero bs=$key count=${test_config[$key]}"
        echo "$cmd"
        $cmd

        echo "========="
        cmd="dd if=/dev/zero of=$tempfile bs=$key count=${test_config[$key]} oflag=dsync"
        echo "$cmd"
        $cmd

        echo "========="

        cmd="dd if=/dev/zero of=$tempfile bs=$key count=${test_config[$key]} oflag=direct"
        echo "$cmd"
        $cmd

    done
