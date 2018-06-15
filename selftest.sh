#!/bin/sh

PORT_PARAM=""
USER_PARAM=""
PASS_PARAM=""
PKEY_PARAM=""
if [ ! -z ${SELFTEST_PORT+x} ]; then
    PORT_PARAM="-c lab.port=${SELFTEST_PORT}"
fi
if [ ! -z ${SELFTEST_USER+x} ]; then
    USER_PARAM="-c lab.user=\"${SELFTEST_USER}\""
fi
if [ ! -z ${SELFTEST_PASSWORD+x} ]; then
    PASS_PARAM="-c lab.password=\"${SELFTEST_PASSWORD}\""
fi
if [ ! -z ${SELFTEST_KEY+x} ]; then
    PKEY_PARAM="-c lab.keyfile=\"${SELFTEST_KEY}\""
fi

python3 -c "__import__('tbot.main').main.main()" local corvus selftest $PORT_PARAM $USER_PARAM $PASS_PARAM $PKEY_PARAM
