# vcon command line tool

## Introduction
The vcon command provides the ability to create and modify JSON format vCons.  The command works like a filter or pipe with an input and output, which is often a JSON format vcon in either the unsigned, signed or encrypted form.  Command operators are specified to modify the input and create the output.  By defulat the input is assumed on stdin and output is provided on stdout.  The -n, -i and -o options override the input and output source.

## Usage:

```
vcon [I/O Options] [Operations]

```

## I/O Options

    **-n** create a new vCon and do not read input from file or stdin (mutually exclusive with -i option)

    **-i FILE** read a vCon from the given file name instead of the default stdin (mutually exclusive with -n option)

    **-o FILE** write the result of the command operation to the given file name instead of the default stdout

## Command Operation

    **add in-email FILE** read a raw SMTP/email message from the given file name and add it to the vCon dialog Object array, add the parties found in the From, To and CC fields to the vCon parties Object array, if the input vCon does not already have a subject set, read the Subject header from the SMTP message and set the vCon subject parameter.  The dialog Object parameters: parties, start, mimetype, encoding and body are all filled in based upon the information in the SMTP message.

    **add in-recording FILE DATE PARTIES** add a inline dialog to the input vCon containing the given recording file name, use the given date as the start time for the recording and the given parties as the participants in the recording.  The date must be the epoch time (seconds since 1970) as an integer or double; or a string RFC2822 or RFC3339 format date. The parties must be a string representing either an integer, an integer array, or an array of integers or integer arrays in JSON format, representing the parties contributing to the media in the corresponding channel.


    **add ex-recording FILE DATE PARTIES URL** add a dialog to the input vCon referencing the given recording file name, use the given date as the start time for the recording and the given parties as the participants in the recording, where the recording is stored at the given HTTPS url.  The date must be the epoch time (seconds since 1970) as an integer or double; or a string RFC2822 or RFC3339 format date. The parties must be a string representing either an integer, an integer array, or an array of integers or integer arrays in JSON format, representing the parties contributing to the media in the corresponding channel.

    **sign KEY [CERT ...]** sign the input vCon using the given private key, attaching the given list of certificates as the cert chain in the x5c parameter.  The output is a vCon in the sgined form (JOSE JWS JSON).

    **verify CERT** verify the signature of the input signed vCon and verify that the certificate in the given file name is in the key chain contained in the x5c or x5u certificate chain contained in the input vCon

    **encrypt CERT** encrypt the input signed vCon using the certificate in the given file name

    **decrypt KEY CERT** decrypt the input encrypted vCon using the private key and certificate in the given file names.

 
