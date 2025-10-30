#include "mml_parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// 1オクターブ内の音名（C, C#, D, D#...）からMIDIノートナンバーへのオフセット
// C4(60)を基準として、配列のインデックスを引くと、その音のノートナンバーになる
// [C, C#, D, D#, E, F, F#, G, G#, A, A#, B]
const int note_offsets[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11};
// ...など、変換に必要なテーブルを定義する

// MML文字列を解析するメイン関数
MmlEvent* parse_mml(const char *mml_string, int sample_rate, size_t *out_num_events) {
    MmlEvent *events = NULL;
    size_t capacity = 10;
    size_t count = 0;

    // 初期化とメモリ確保
    events = (MmlEvent*)malloc(capacity * sizeof(MmlEvent));
    if (!events) {
        fprintf(stderr, "メモリが足りません\n");
        *out_num_events = 0;
        return NULL;
    }

    // 現在の状態を保持する変数
    int current_octave = 4;
    int current_length = 4;
    double current_tempo = DEFAULT_TEMPO; // t120から開始
    int current_volume = DEFAULT_VOLUME; // デフォルト音量を設定
    double current_decay_rate = DEFAULT_DECAY_RATE; // デフォルト減衰率を設定

    // --- 解析ループ ---
    const char *p = mml_string;
    const char *next_p;

    // MML@ の特殊処理 先頭に "MML@" がある場合はスキップ
    if (p[0] == 'M' && p[1] == 'M' && p[2] == 'L' && p[3] == '@') {
        p += 4; // "MML@" の4文字をスキップ
    }

    while (*p != '\0') {
        if (isspace(*p)) {
            p++;
            continue; // 空白はスキップ
        }

        // メモリが足りなくなったら拡張
        if (count >= capacity) {
            capacity *= 2;
            events = (MmlEvent*)realloc(events, capacity * sizeof(MmlEvent));
            if (!events) {
                fprintf(stderr, "メモリ拡張に失敗しました\n");
                *out_num_events = count;
                return NULL;
            }
        }

        char command = tolower(*p);
        p++;

        int note_idx = -1;
        int note_length = current_length;

        const char *p_before_num = p;
        if (isdigit(*p_before_num)) {
            // 数字が続く場合は音長の可能性があるので保存
            note_length = (int)strtol(p_before_num, (char **)&next_p, 10);
            p_before_num = next_p;
        }

        // --- 音長からサンプル数を計算 ---
        double sec_per_quarter = 60.0 / current_tempo;
        double sec_per_note = sec_per_quarter * (4.0 / (double)note_length);
        uint32_t current_duration = (uint32_t)(sec_per_note * sample_rate);
        
        if (*p == '&') {
            if (count > 0) { // 前のイベントが存在する場合
                // 前のイベントに現在の音符の長さ（current_duration）を加算
                events[count - 1].duration_samples += current_duration;
                p++; // &を消費
                continue; // イベント生成をスキップして次のコマンドへ
            }
            // タイ記号が最初に来た場合は無視
            continue;
        }

        // --- 制御コマンド (o, l, t) ---
        if (command == 'o') { // オクターブ oX
            current_octave = (int)strtol(p, (char **)&next_p, 10);
            p = next_p;
            continue;
        } else if (command == 'l') { // 音長 lX
            current_length = (int)strtol(p, (char **)&next_p, 10);
            p = next_p;
            continue;
        } else if (command == 't') { // テンポ tX
            current_tempo = (double)strtol(p, (char **)&next_p, 10);
            p = next_p;
            continue;
        } else if (command == 'v') { // 音量 vX の処理
            current_volume = (int)strtol(p, (char **)&next_p, 10);
            p = next_p;
            continue;
        } else if (command == '@') { // 音色 @X の処理 (今回は無視)
            // 音色の数字を読み飛ばす
            (void)strtol(p, (char **)&next_p, 10);
            p = next_p;
            continue;
        } else if (command == '>') { // オクターブアップ
            current_octave++;
            continue;
        } else if (command == '<') { // オクターブダウン
            current_octave--;
            continue;
        }

        // MMLコマンドごとの解析ロジック
        if (command >= 'a' && command <= 'g' || command == 'n') {
            if (command == 'n') {
                // nXX の処理
                int n_note = (int)strtol(p, (char **)&next_p, 10);
                p = next_p;
                events[count].note_number = n_note;
            } else {
                // 'c'を0、'd'を2、'e'を4、'f'を5、'g'を7、'a'を9、'b'を11とする
                // ノート名をインデックスに変換
                if (command == 'c') note_idx = 0;
                else if (command == 'd') note_idx = 2;
                else if (command == 'e') note_idx = 4;
                else if (command == 'f') note_idx = 5;
                else if (command == 'g') note_idx = 7;
                else if (command == 'a') note_idx = 9;
                else if (command == 'b') note_idx = 11;

                // MIDIノートナンバーを計算 (C4=60を基準)
                if (note_idx != -1) {
                    events[count].note_number = 60 + (current_octave - 4) * 12 + note_idx;
                } else {
                    continue;
                }

                if (*p == '+' || *p == '#') {
                    events[count].note_number += 1; // シャープは半音上げ
                    p++;
                } else if (*p == '-') {
                    events[count].note_number -= 1; // フラットは半音下げ
                    p++;
                }
            }

        } else if (command == 'r') { // 休符の処理
            events[count].note_number = 0; // 休符はNOTE=0
        } else if (command == ',') { // トラック区切りの処理
            // トラック区切りは無視
            continue;
        } else {
            // 未対応のコマンドはスキップ
            continue;
        }

        // イベントをリストに追加
        events[count].duration_samples = current_duration;
        events[count].volume = current_volume;
        events[count].decay_rate = current_decay_rate;
        count++;

        // 付点音符(.)の処理
        // sec_per_note は元の音符の長さ（例：c4 なら 0.5秒）
        double ext_factor = 0.5; // 延長倍率の初期値 (付点用)
        while (*p == '.') {
            // 付点音符は、元の音符の長さの 1/2, 1/4, 1/8... を加算
            // (sec_per_note) の 1/2^N を加算
            events[count - 1].duration_samples += (uint32_t)(sec_per_note * ext_factor * sample_rate);
            ext_factor /= 2.0; // 次の付点はさらに半分
            p++;
        }
    }

    // 最後にメモリを整理する
    events = (MmlEvent*)realloc(events, count * sizeof(MmlEvent));
    *out_num_events = count;

    printf("MML解析完了イベント数: %zu\n", count);
    return events;
}

// メモリ解放関数
void free_mml_events(MmlEvent *events) {
    if (events) {
        free(events);
    }
}