# aosp-docker

A python 2 script which can be used to build various AOSP versions inside a docker container.

Very early state.

## Dependencies

* python2: docker-py
* docker

## Usage
	Usage: aosp [COMMAND] [arg...]
	Commands:
		init	Initialize a container in current directory (should be AOSP dir)
		exec	Executes a command inside the aosp build container
		bash	Starts a bash shell inside the container
		clean	Removes container
		info	Shows information about the aosp container

## Example usage

### Download Android 4.4.4
	~ $> mkdir ~/aosp && cd ~/aosp
	~/aosp $> aosp init 4.4
	~/aosp $> aosp exec repo init -u https://android.googlesource.com/platform/manifest/ -b android-4.4.4_r2
	~/aosp $> aosp exec repo sync

### Build AOSP
	~/aosp $> aosp exec . build/envsetup.sh
	~/aosp $> aosp exec lunch
	~/aosp $> aosp exec make -j5

### Inside a sub directory
	~/aosp $> cd packages/apps/Calculator
	~/aosp/packages/apps/Calculator $> mmm

### Drop into a bash
	~/aosp $> aosp bash
	/aosp# ▉ 

### Remove container
	aosp clean