#include <stdio.h>
#include <string.h>

int main( int nargs, const char * const args[])
{
const char * filename;
FILE * fp;
int len;
int numPackets;
int i,j;

int sums[3];
int charcounts[3][256];

memset( charcounts, 0x00, sizeof( charcounts ) );
memset( sums, 0x00, sizeof( sums ) );

if( nargs!=2 )
	{
	printf("Usage: %s uartdump\n", args[0] );
	return 1;
	}

filename = args[1];
fp= fopen( filename, "r");
if( fp == NULL )
	{
	printf("Couldn't open %s\n",filename);
	return 2;
	}

if( 0 != fseek( fp, 0, SEEK_END ) )
	{
	printf("Couldn't seek to end\n");
	return 3;
	}

len = ftell( fp );
if( len < 23 )
	{
	printf("File too small to be LCD2CLIP image\n");
	return 4;
	}

len -= 23;
if( len % 3 )
	{
	printf("Data segment is not divisible by 3!\n");
	return 5;
	}

numPackets = len / 3;
printf("There are %i packets\n", numPackets );

if( 0 != fseek( fp, 21, SEEK_SET ) )
	{
	printf("Couldn't seek to datasegment\n");
	return 6;
	}

for( i = 0; i < numPackets; ++i )
	{
	unsigned char bytes[3];
	int numBytes;

	numBytes = fread( bytes, 3, 1, fp );
	charcounts[0][bytes[0]]++;
	charcounts[1][bytes[1]]++;
	charcounts[2][bytes[2]]++;
	printf("%02x %02x %02x\n", bytes[0], bytes[1], bytes[2] );
	}

for( j = 0; j < 3; ++j )
	{
	printf("Printing Stats for Column %i\n",j);
	for( i = 0; i < 256; ++i )
		{
		printf("%02x:%i\n",i,charcounts[j][i]);
		}
	}

fclose( fp );
}
