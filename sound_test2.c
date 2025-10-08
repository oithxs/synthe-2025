#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <alsa/asoundlib.h>

// 音声再生の基本パラメータ
#define DURATION_SEC    1.0     // 再生時間（秒）
#define SAMPLE_RATE     44100   // サンプリングレート (Hz)
#define CHANNELS        1       // チャンネル数 (1: モノラル, 2: ステレオ)
#define TONE_FREQ       440.0   // 音の周波数 (Hz) - 440Hzは「ラ」(A4)の音
#define AMPLITUDE       32760   // 振幅 (16bitの最大値に近い値)

int main() {
    // ALSA関連の変数を宣言
    snd_pcm_t *handle;
    snd_pcm_hw_params_t *params;
    int err;
    
    // PCMデバイスを再生用に開く。 "default" は標準の出力デバイスを意味する
    if ((err = snd_pcm_open(&handle, "default", SND_PCM_STREAM_PLAYBACK, 0)) < 0) {
        fprintf(stderr, "PCMデバイスを開けません: %s\n", snd_strerror(err));
        return 1;
    }

    // ハードウェアパラメータ構造体を確保
    snd_pcm_hw_params_alloca(&params);
    // デバイスの現在のパラメータを取得
    snd_pcm_hw_params_any(handle, params);

    // パラメータを設定
    snd_pcm_hw_params_set_access(handle, params, SND_PCM_ACCESS_RW_INTERLEAVED); // アクセスタイプ: インターリーブ
    snd_pcm_hw_params_set_format(handle, params, SND_PCM_FORMAT_S16_LE);      // フォーマット: 16bit, リトルエンディアン
    snd_pcm_hw_params_set_channels(handle, params, CHANNELS);                 // チャンネル数
    snd_pcm_hw_params_set_rate_near(handle, params, (unsigned int[]){SAMPLE_RATE}, 0); // サンプリングレート

    // 設定したパラメータをデバイスに書き込む
    if ((err = snd_pcm_hw_params(handle, params)) < 0) {
        fprintf(stderr, "ハードウェアパラメータを設定できません: %s\n", snd_strerror(err));
        return 1;
    }

    // --- ここからが波形データの生成 ---
    const int buffer_size = DURATION_SEC * SAMPLE_RATE;
    int16_t buffer[buffer_size]; // 波形データを格納するバッファ

    printf("波形データを生成中...\n");
    for (int i = 0; i < buffer_size; ++i) {
        // 正弦波を計算
        double sin_val = sin(2.0 * M_PI * TONE_FREQ * i / SAMPLE_RATE);
        //printf("sin_val = %f\n", sin_val);
        // 16bit整数 (-32767 ~ 32767) の範囲に変換してバッファに格納
        buffer[i] = (int16_t)(sin_val * AMPLITUDE);
    }
    printf("生成完了。\n");

    // --- ここで波形データを再生 ---
    printf("再生を開始します...\n");
    err = snd_pcm_writei(handle, buffer, buffer_size);
    printf("err = %d\n", err);
    int play = snd_pcm_start(handle);
    if (err < 0) {
        // バッファが一杯なら回復を試みる
        printf("playing sound...");
        snd_pcm_recover(handle, err, 0);
        err = snd_pcm_writei(handle, buffer, buffer_size);
    }

    // 全てのフレームが再生されるのを待つ
    snd_pcm_drain(handle);
    printf("再生が完了しました。\n");

    // PCMデバイスを閉じる
    snd_pcm_close(handle);

    return 0;
}
