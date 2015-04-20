aosp-docker
===========

A python2 script which can be used to build various AOSP versions inside a docker container.

Very early state.

Example usage
-------------

	mkdir ~/aosp && cd ~/aosp
	aosp init 4.4
	aosp exec repo init -u https://android.googlesource.com/platform/manifest/ -b android-4.4.4_r2
	aosp exec repo sync
	aosp exec . build/envsetup.sh
	aosp exec lunch
	aosp exec make -j5
	aosp clean