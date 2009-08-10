#!/bin/sh

echo "building calculator.edj..."
edje_cc\
        -id edje/default/images\
        -id ../../resources/images\
        -fd ../../resources/fonts\
        edje/default/calculator.edc\
        -o calculator.edj
