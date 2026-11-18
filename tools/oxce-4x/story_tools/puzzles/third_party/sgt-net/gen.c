/* STORY wrapper: generate one puzzle description with Simon Tatham's generator (MIT licence, see LICENCE). */
#include <stdlib.h>
#include <string.h>
#include "puzzles.h"
extern const struct game thegame;
static char out[65536];
__attribute__((export_name("buf"))) char *buf(void) { return out; }
/* params and seed are read from out: "params\0seed\0"; the description is written back into out */
__attribute__((export_name("gen"))) int gen(void) {
    char params[256], seed[256];
    strncpy(params, out, 255); params[255]=0;
    strncpy(seed, out + strlen(out) + 1, 255); seed[255]=0;
    game_params *p = thegame.default_params();
    thegame.decode_params(p, params);
    random_state *rs = random_new(seed, (int)strlen(seed));
    char *aux = NULL;
    char *desc = thegame.new_desc(p, rs, &aux, 1);
    strncpy(out, desc, 32000); out[32000]=0;
    int n = (int)strlen(out);
    /* then the generator's aux (Net: the unshuffled solution), after a NUL */
    if (aux) { strncpy(out + n + 1, aux, 32000); out[n + 1 + 32000] = 0; } else out[n + 1] = 0;
    sfree(desc); if (aux) sfree(aux); random_free(rs); thegame.free_params(p);
    return n;
}
void fatal(char *fmt, ...) { abort(); }
void get_random_seed(void **randseed, int *randseedsize) { *randseed = NULL; *randseedsize = 0; }
void frontend_default_colour(frontend *fe, float *output) { output[0]=output[1]=output[2]=0.8f; }
void deactivate_timer(frontend *fe) {}
void activate_timer(frontend *fe) {}
char *midend_rewrite_statusbar(midend *me, char *text) { return dupstr(text); }
