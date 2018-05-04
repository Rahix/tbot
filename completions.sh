_tbot()
{
    local cur prev words cword
    _init_completion || return

    # 1) LAB
    # 2) BOARD
    # 3+) TESTCASE
    local current_mode=0
    for word in ${words[*]}; do
        if [[ $word != -* && $word != $cur ]]; then
            current_mode=$(($current_mode + 1))
        fi
    done

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '-h -c -d -l -v -q
            --help --config --confdir --labconfdir
            --boardconfdir --tcdir --logfile --verbose
            --quiet --list-testcases --list-labs
            --list-boards' -- "$cur" ) )
    else
        case $current_mode in
            1)  # LAB
                local labs=$(ls config/labs | grep \\.py | sed 's/\.py$//')
                COMPREPLY=( $( compgen -W "$labs" -- "$cur") )
                ;;
            2)  # BOARD
                local boards=$(ls config/boards | grep \\.py | sed 's/\.py$//')
                COMPREPLY=( $( compgen -W "$boards" -- "$cur") )
                ;;
            *)  # TESTCASE
                # Collecting testcases can be really slow, so we cache them for
                # a small amount of time (10 seconds)
                local cache_age=$(($(date +%s) - ${__tbot_testcase_cache_time:-0}))
                if [[ -z $__tbot_testcase_cache || $cache_age -gt 10 ]]; then
                    __tbot_testcase_cache=$(tbot none none --list-testcases)
                    __tbot_testcase_cache_time=$(date +%s)
                fi
                COMPREPLY=( $( compgen -W "$__tbot_testcase_cache" -- "$cur") )
                ;;
        esac
    fi
} &&
complete -F _tbot tbot

#ex: filetype=sh
