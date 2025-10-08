#include <stdio.h>
#include <string.h>

// (1)
#include <alsa/asoundlib.h>

#define	BUFFER_SAMPLES	588

int main(int argc, char *argv[])
{
	if(argc == 1){
		printf("Usage: %s <wav> [dev]\n", argv[0]);
		return -1;
	}

	// WAVファイルをオープン
	FILE *fp = fopen(argv[1], "rb");
	if(fp == NULL){
		printf("Can't open wav: %s\n", argv[1]);
		return -1;
	}

	// WAVファイルからパラメータのチャンクを読み取る
	char cid[5] = "CHID";
	uint32_t clen;

	printf("---- WAV FILE ----\n");
	fread(cid, 4, 1, fp); printf("'%s'", cid);		// 'RIFF'
	fread(&clen, sizeof(clen), 1, fp);
	printf(", len = %d\n", clen);

	fread(cid, 4, 1, fp); printf("'%s'\n", cid);	// 'WAVE'
	fread(cid, 4, 1, fp); printf("'%s'", cid);		// 'fmt '
	fread(&clen, sizeof(clen), 1, fp);
	printf(", len = %d\n", clen);

	uint8_t *cbuf = new uint8_t[clen];
	fread(cbuf, clen, 1, fp);

	uint16_t formatTag		= *(uint16_t *)&cbuf[0];
	uint16_t channels 		= *(uint16_t *)&cbuf[2];
	uint32_t samplesPerSec	= *(uint32_t *)&cbuf[4];
	uint32_t avgBytesPerSec	= *(uint32_t *)&cbuf[8];
	uint16_t blockAlign 	= *(uint16_t *)&cbuf[12];
	uint16_t bitsPerSample	= *(uint16_t *)&cbuf[14];
	delete[] cbuf;
	
	printf("  formatTag = %d\n", formatTag);
	printf("  channels = %d\n", channels);
	printf("  samplesPerSec = %d\n", samplesPerSec);
	printf("  avgBytesPerSec = %d\n", avgBytesPerSec);
	printf("  blockAlign = %d\n", blockAlign);
	printf("  bitsPerSample = %d\n", bitsPerSample);

	fread(cid, 4, 1, fp); printf("'%s'", cid);		// 'data'
	fread(&clen, sizeof(clen), 1, fp);
	printf(", len = %d\n", clen);

	if(strcmp(cid, "data") != 0){
		printf("WAV file format error.\n");
		fclose(fp);
		return -1;
	}
	int data_len = clen;

	// 音楽データの読み取り用バッファの領域を確保する
	uint8_t *buffer = new uint8_t[blockAlign * BUFFER_SAMPLES];

	// (2)
	snd_pcm_t *hndl = NULL;
	snd_output_t *output = NULL;
	const char *dev = "default";
	if(argc > 2){
		dev = argv[2];
	}

	int soft_resample = 1;
	unsigned int latency = 50000;

	// (3)
	snd_pcm_format_t format = SND_PCM_FORMAT_S16_LE;
	if((bitsPerSample == 24) && (blockAlign == 6)){
		format = SND_PCM_FORMAT_S24_3LE;
	}

	// (4)
	int ret = snd_pcm_open(&hndl, dev, SND_PCM_STREAM_PLAYBACK, 0);
	if(ret != 0){
		printf("snd_pcm_open: error %d\n", ret);
		goto End;
	}

	// (5)
	ret = snd_pcm_set_params(hndl, format, SND_PCM_ACCESS_RW_INTERLEAVED, channels, samplesPerSec, soft_resample, latency);
	if(ret != 0){
		printf("snd_pcm_set_params: error %d\n", ret);
		goto End;
	}

	// (6)
	snd_output_stdio_attach(&output, stdout, 0);
	printf("---- PCM DUMP ----\n");
	snd_pcm_dump(hndl, output);

	for(int n = 0; n < data_len; n += (blockAlign * BUFFER_SAMPLES)){
		// 音楽データの読み取り
		ret = fread(buffer, blockAlign, BUFFER_SAMPLES, fp);
		if(ret > 0){
			// (7)
			snd_pcm_writei(hndl, (const void *)buffer, ret);
		}
	}
	// (8)
	snd_pcm_drain(hndl);

End:
	// (9)
	if(hndl != NULL) snd_pcm_close(hndl);
	if(fp != NULL) fclose(fp);
	if(buffer != NULL) delete[] buffer;

	return 0;
}
