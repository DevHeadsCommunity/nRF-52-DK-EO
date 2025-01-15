#include <zephyr/shell/shell.h>
#include "util.h"

#define UPTIME_STRING_LEN 64

static int cmd_hil_ping(const struct shell *sh, size_t argc,
                         char **argv)
{
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);

    shell_print(sh, "pong");
    return 0;
}

static int cmd_hil_uptime(const struct shell *sh, size_t argc,
                           char **argv)
{
    char uptime_str[UPTIME_STRING_LEN];

    int64_t uptime = k_uptime_get();
    uptime_to_string(uptime, uptime_str);

    shell_print(sh, "%s", uptime_str);
    return 0;
}

static int cmd_hil_uptime_ms(const struct shell *sh, size_t argc,
                           char **argv)
{
    int64_t uptime = k_uptime_get();

    shell_print(sh, "%lld\n", uptime);
    return 0;
}

/* Creating subcommands (level 1 command) array for command "hil". */
SHELL_STATIC_SUBCMD_SET_CREATE(sub_hil,
        SHELL_CMD(ping,   NULL, "Ping command.", cmd_hil_ping),
        SHELL_CMD(uptime,   NULL, "Uptime command.", cmd_hil_uptime),
        SHELL_CMD(uptime-ms,   NULL, "Uptime MS command.", cmd_hil_uptime_ms),
        SHELL_SUBCMD_SET_END
);

/* Creating root (level 0) command "hil" without a handler */
SHELL_CMD_REGISTER(hil, &sub_hil, "HIL commands", NULL);