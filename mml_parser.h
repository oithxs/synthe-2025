#ifndef MML_PARSER_H
#define MML_PARSER_H

#include <stdint.h>
#include <stddef.h>

// MML演奏イベントの構造体
typedef struct {
    int note_number;
    uint32_t duration_samples;
    int volume;
    double decay_rate;
} MmlEvent;

// テンポの初期値 (BPM)
#define DEFAULT_TEMPO 120
#define DEFAULT_VOLUME 100
#define DEFAULT_DECAY_RATE 0.99995 // 1サンプルあたりの音量減少率（例）

// MML文字列を解析して、MmlEventのリストを生成する関数
// 戻り値: MmlEventの配列
// *out_num_events: 生成されたイベントの個数を格納するポインタ
MmlEvent* parse_mml(const char *mml_string, int sample_rate, size_t *out_num_events);

// メモリ解放関数(mallocで確保した分をfreeする)
void free_mml_events(MmlEvent *events);

#endif // MML_PARSER_H