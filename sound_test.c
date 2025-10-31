#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <alsa/asoundlib.h>
#include "mml_parser.h"

// 音声再生の基本パラメータ
#define DURATION_SEC    1.0     // 再生時間（秒）
#define SAMPLE_RATE     44100   // サンプリングレート (Hz)
#define CHANNELS        1       // チャンネル数 (1: モノラル, 2: ステレオ)
#define TONE_FREQ       440.0   // 音の周波数 (Hz) - 440Hzは「ラ」(A4)の音
#define AMPLITUDE       32760   // 振幅 (16bitの最大値に近い値)
#define TABLE_SIZE        32    // ウェーブテーブルのサイズ（2のべき乗が一般的）
#define INC_AMPLITUDE   4096    // 増分用振幅
#define FILE_TABLE_SIZE   32    // ファイルから読み込むウェーブテーブルのサイズ

// グローバル変数としてウェーブテーブルを定義
// GUIから変更する場合、この配列を書き換える
float wavetable_f[TABLE_SIZE];

// --- 固定小数点演算のための設定 ---
// フェーズアキュムレータの小数部として使うビット数
#define FRACTIONAL_BITS 32

// グローバルなウェーブテーブル (整数型)
int16_t wavetable[TABLE_SIZE];

// ウェーブテーブルを初期化する関数
void init_wavetable_f() {
    printf("ウェーブテーブルを生成中...\n");
    for (int i = 0; i < TABLE_SIZE; ++i) {
        // 現在位置を 0.0 ~ 2*PI の範囲に変換
        double angle = 2.0 * M_PI * i / TABLE_SIZE;
        // printf("M_PI = %f\n", M_PI);

        // 例：基音(sin) + 2倍音(sin*2) + 3倍音(sin*3) を合成した波形
        wavetable_f[i] = 0.5 * sin(angle) + 0.3 * sin(2 * angle) + 0.2 * sin(3 * angle);
    }
}

// ウェーブテーブルを初期化する関数
void init_wavetable() {
    printf("整数型ウェーブテーブルを生成中...\n");
    for (int i = 0; i < TABLE_SIZE; ++i) {
        double angle = 2.0 * M_PI * i / TABLE_SIZE;
        // printf("M_PI = %f\n", M_PI);
        // -1.0 ~ 1.0 の値を AMPLITUDE 倍して int16_t に変換
        wavetable[i] = (int16_t)((0.5 * sin(angle) + 0.3 * sin(2 * angle) + 0.2 * sin(3 * angle)) * AMPLITUDE);
        //printf("[%d]: %d\n", i, wavetable[i]);
        //printf("[%d]: %f\n", i, (0.5 * sin(angle) + 0.3 * sin(2 * angle) + 0.2 * sin(3 * angle)));
    }
}

// テキストファイルから波形数値列を読み込む関数
int load_wavetable_from_file(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "ファイルを開けません: %s\n", filename);
        return -1;
    }
    for (int i = 0; i < FILE_TABLE_SIZE; ++i) {
        if (fscanf(fp, "%d", &wavetable[i]) != 1) {
            fprintf(stderr, "ウェーブテーブルの読み込みに失敗しました。\n");
            fclose(fp);
            return -1;
        }
        wavetable[i] *= INC_AMPLITUDE; // 振幅を増加
    }
    // FILE_TABLE_SIZEからTABLE_SIZEに適応するようコピー
    for (int i = FILE_TABLE_SIZE; i < TABLE_SIZE; ++i) {
        wavetable[i] = wavetable[i % FILE_TABLE_SIZE];
        printf("[%d]: %d\n", i, wavetable[i]);
    }
    fclose(fp);
    return 0;
}

// MIDIノートナンバーを周波数に変換するヘルパー関数
double note_to_freq(int note) {
    return 440.0 * pow(2.0, (note - 69.0) / 12.0);
}

void debug_play_note(snd_pcm_t *handle, snd_pcm_hw_params_t *params, int err) {
    printf("\n--- 過去のテストコード実行（デバッグ用） ---\n");
    // --- 音声データの生成と再生 ---
    int duration_sec = 3; // 3秒間再生
    long buffer_size = duration_sec * SAMPLE_RATE;
    int16_t *buffer = malloc(buffer_size * sizeof(int16_t));
    
    // 「ドレミ」を演奏 (C4, D4, E4)
    int notes[] = {60, 62, 64}; // MIDIノートナンバー (60=中央のド)
    
    /*
    double phase = 0.0;
    for (int i = 0; i < buffer_size; ++i) {
        // 1秒ごとに音程を変える
        int current_note = notes[(i / SAMPLE_RATE) % 3];
        double frequency = note_to_freq(current_note);

        // フェーズ増分を計算
        double phase_increment = (double)TABLE_SIZE * frequency / SAMPLE_RATE;

        // テーブルから値を読み出し、バッファに書き込む
        buffer[i] = (int16_t)(wavetable[(int)phase] * AMPLITUDE);

        // フェーズを更新
        phase += phase_increment;
        if (phase >= TABLE_SIZE) {
            phase -= TABLE_SIZE;
        }
    }
    * */
    // フェーズアキュムレータを符号なし64ビット整数で定義
    uint64_t phase = 0;
    
    for (int i = 0; i < buffer_size; ++i) {
        int current_note = notes[(i / SAMPLE_RATE) % 3];
        double frequency = note_to_freq(current_note);

        // 固定小数点のフェーズ増分を計算
        // doubleで一度計算してからuint64_tにキャストすることで精度を保つ
        uint64_t phase_increment = (uint64_t)(((double)TABLE_SIZE * frequency / SAMPLE_RATE) * (1LL << FRACTIONAL_BITS));

        // フェーズの整数部をインデックスとして使用 (小数部をビットシフトで切り捨て)
        uint32_t index = (uint32_t)(phase >> FRACTIONAL_BITS);

        // テーブルから値を読み出し、バッファに書き込む
        // indexがテーブルサイズを超えないように剰余を取る
        buffer[i] = wavetable[index % TABLE_SIZE];

        // フェーズを更新 (整数の足し算のみ)
        phase += phase_increment;
    }
    
    printf("「ドレミ」を再生します...\n");
    snd_pcm_writei(handle, buffer, buffer_size);
    
    // クリーンアップ
    snd_pcm_drain(handle);
    snd_pcm_close(handle);
    free(buffer);

    // --- ここからが波形データの生成 ---
    /*
    const int buffer_size = DURATION_SEC * SAMPLE_RATE;
    int16_t buffer[buffer_size]; // 波形データを格納するバッファ

    printf("波形データを生成中...\n");
    for (int i = 0; i < buffer_size; ++i) {
        // 正弦波を計算
        double sin_val = sin(2.0 * M_PI * TONE_FREQ * i / SAMPLE_RATE);
        //printf("sin_val = %f\n", sin_val);
        // 16bit整数 (-32767 ~ 32767) の範囲に変換してバッファに格納
        buffer[i] = (int16_t)(sin_val * AMPLITUDE);
        printf("buffer[%d] = %d\n", i, buffer[i]);
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
    */
    printf("-------------------------------------------\n");
}

int main(int argc, char *argv[]) {
    // ALSA関連の変数を宣言
    snd_pcm_t *handle;
    snd_pcm_hw_params_t *params;
    int err;
    
    // ウェーブテーブルを初期化
    //init_wavetable();
    load_wavetable_from_file("preset1.txt");
    
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

    // コマンドライン引数の処理
    if (argc < 3) {
        fprintf(stderr, "使い方: %s <wavetableファイル名> <mmlファイル名>\n", argv[0]);
        // デバッグ用に過去のテストコードを実行
        debug_play_note(handle, params, err);
        return 1;
    }
    const char *wavetable_file = argv[1];
    const char *mml_input = argv[2];

    // --- wavetableテキストの読み込み ---
    if (load_wavetable_from_file(wavetable_file) != 0) {
        fprintf(stderr, "ウェーブテーブルの読み込みに失敗しました: %s\n", wavetable_file);
        return 1;
    }
    printf("ウェーブテーブルをファイルから読み込みました: %s\n", wavetable_file);

    // --- MMLファイルの解析とイベントリストの取得 ---

    // --- MMLファイルを読み込む ---
    FILE *fp = fopen(mml_input, "rb");
    if (!fp) {
        fprintf(stderr, "MMLファイルを開けません: %s\n", mml_input);
        return 1;
    }
    // ファイルサイズを取得
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    rewind(fp);

    // MML文字列を格納するバッファを確保
    char *mml_string = (char *)malloc(file_size + 1);
    if (!mml_string) {
        fprintf(stderr, "メモリが足りません\n");
        fclose(fp);
        return 1;
    }

    // ファイル内容を読み込む
    size_t read_size = fread(mml_string, 1, file_size, fp);
    mml_string[read_size] = '\0'; // NULL終端
    fclose(fp);

    // --- MML解析と音声データの生成 ---
    MmlEvent *events = NULL;
    size_t num_events = 0;

    printf("MMLを解析中...: %s\n", mml_input);
    // MML文字列を解析してイベントリストを取得
    events = parse_mml(mml_string, SAMPLE_RATE, &num_events);
    free(mml_string); // 解析後はMML文字列のメモリを解放
    if (!events) {
        fprintf(stderr, "MMLの解析に失敗しました。\n");
        return 1;
    }

    // 総再生時間を計算
    long total_samples = 0;
    for (size_t i = 0; i < num_events; ++i) {
        total_samples += events[i].duration_samples;
    }
    printf("総再生時間: %ld サンプル (%f 秒)\n", total_samples, (double)total_samples / SAMPLE_RATE);

    // 解析結果を一覧表示
    printf("--- 解析イベント詳細 ---\n");
    for (size_t i = 0; i < num_events; ++i) {
        double duration_sec = (double)events[i].duration_samples / SAMPLE_RATE;
        // とりあえず数値で確認
        if (events[i].note_number > 0) {
            printf("イベント%zu: NOTE=%d (周波数=%f Hz), 長さ=%u サンプル (%f 秒)\n", i, events[i].note_number, note_to_freq(events[i].note_number), events[i].duration_samples, duration_sec
            );
        } else {
            printf("イベント%zu: REST, 長さ=%u サンプル (%f 秒)\n", i, events[i].duration_samples, duration_sec);
        }
    }
    printf("----------------------\n");

    // 再生用バッファを確保
    int16_t *buffer = (int16_t *)malloc(total_samples * sizeof(int16_t));
    if (!buffer) {
        fprintf(stderr, "再生バッファの確保に失敗しました。\n");
        free_mml_events(events);
        return 1;
    }

    // --- MMLイベントを使った波形生成ループ ---
    uint64_t phase = 0;
    long current_sample_index = 0;

    // MMLイベントを順に処理するループ
    for (size_t i = 0; i < num_events; ++i) {
        MmlEvent *event = &events[i];
        // ノートナンバーから周波数を計算
        double frequency = 0.0;
        uint64_t phase_increment = 0;

        if (event->note_number > 0) {
            frequency = note_to_freq(event->note_number);
            // 固定小数点のフェーズ増分を計算 (イベント開始時に一度だけ計算)
            phase_increment = (uint64_t)(((double)TABLE_SIZE * frequency / SAMPLE_RATE) * (1LL << FRACTIONAL_BITS));
        }
        double volume_scale = (double)(event->volume) / DEFAULT_VOLUME; // 音量スケール (0.0 ~ 1.0)
        double current_amplitude = volume_scale; // 現在の振幅

        for (uint32_t j = 0; j < event->duration_samples; ++j) {
            
            // 音を鳴らす or 休符（ゼロ埋め）
            if (event->note_number > 0) {
                // 音を鳴らす処理
                uint32_t index = (uint32_t)(phase >> FRACTIONAL_BITS);
                buffer[current_sample_index] = (int16_t)(wavetable[index % TABLE_SIZE] * current_amplitude);
                current_amplitude *= event->decay_rate; // 1サンプルごとに音量を減衰

                // フェーズを更新
                phase += phase_increment;
            } else {
                // 休符処理 (音をゼロにする)
                buffer[current_sample_index] = 0;
            }
            
            current_sample_index++;
            if (current_sample_index >= total_samples) break; // バッファオーバーフロー対策
        }
        if (current_sample_index >= total_samples) break;
    }

    printf("再生を開始します...\n");
    snd_pcm_writei(handle, buffer, total_samples);

    // クリーンアップ
    snd_pcm_drain(handle);
    snd_pcm_close(handle); // PCMデバイスを閉じる
    free(buffer);
    free_mml_events(events); // 解析結果のメモリも解放
    printf("クリーンアップ完了\n");

    return 0;
}
