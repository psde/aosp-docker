# aosp-docker

A Python 2/3 script which can be used to build various AOSP versions inside a docker container.

Very early state, expect things to change and break with new commits.

## Dependencies

* docker 1.6
* python: docker-py 1.3

## Why?

In order to compile AOSP a very specific tool chain is needed. Bash is needed for every version, Android 4.0 needs gcc 4.4 and Oracle JDK 6, Android 5.0 gcc 4.8 and OpenJDK 7. Using a virtual machine for building has a large overhead, most developers will use a full Ubuntu installation with XServer and everything, which can take up to 20 Gb disk space and comes with processor and memory overhead. Having to work on and build multiple different AOSP versions I opted to hack together this python script which uses docker to build the different versions.

## How?

The container image already has the needed tool chain installed and could be used without a script. But as we do not want to work inside the container the script uses `docker exec` to run commands inside the container. In order to save the bash environment every `aosp exec` command is wrapped:

	source /env.bash && cd {dir} && {cmd} && declare -p | sed -e \'/declare -[a-z]*r/d\' > /env.bash && declare -f >> /env.bash

This will first source the saved environment, change to the requested directory, executes the command and then saves the environment (including functions) back to disk. The `sed` regex is needed to only save environment variables which are not read-only.

When dropping into a bash with `aosp bash`, the script will execute `/bin/bash --rcfile /rc.bash`. This rcfile will trap the exit signal in order to save the environment after the bash is closed:

	trap "declare -p | sed -e '/declare -[a-z]*r/d' > /env.bash && declare -f >> /env.bash" EXIT

The script will create a user inside the docker container with the same uid/gid as your user, which will be used when interacting with the `exec` and `bash` commands. In case you want root access, `aosp root exec` and `aosp root bash` can be used, but the environment will not be saved.

## Todo and Known Issues

* Dockerfiles should not be generated at runtime, but maybe checked into the repository
* git and bash configs are currently not copied to the container

## Usage
	Usage: aosp [COMMAND] [arg...]
	Commands:
		init	Initialize a container in current directory (should be AOSP dir)
		exec	Executes a command inside the aosp build container
		bash	Starts a bash shell inside the container
		clean	Removes container
		info	Shows information about the aosp container

	For root access please use `root exec` and `root bash`.

## Example usage

### Download AOSP 4.4.4
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
	~/aosp/packages/apps/Calculator $> aosp exec mmm

### Drop into a bash and continue building
	~/aosp $> aosp exec lunch
	~/aosp $> aosp bash
	/aosp# make -j5

### Remove container
	~/aosp $> aosp clean
