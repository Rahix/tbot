_tbot()
{
    local cur prev words cword
    _init_completion || return

    # Completions for path arguments
    if [[ "$prev" == @(-d|--tcdir|--confdir|--labconfdir|--boardconfdir) ]]; then
        _filedir -d
        # Remove __pycache__ for convenience
        COMPREPLY=(${COMPREPLY[@]/*__pycache__*/})
        return
    fi

    # We can't complete these arguments
    if [[ "$prev" == @(-c|-p|--config|--param) ]]; then
        return
    fi

    # Completions for the logfile
    if [[ "$prev" == @(-l|--logfile) ]]; then
        _filedir
        return
    fi

    # Check what is required next
    # and catch values that we need for later completions
    # 1) LAB
    # 2) BOARD
    # 3+) TESTCASE
    local current_mode=0
    local index=0
    local tcdirs_additional=""
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" != -* && "$current_word" != "$cur" ]]; then
            current_mode=$(($current_mode + 1))
        # If this argument is one that carries a parameter
        # catch that parameter and skip the next
        elif [[ "$current_word" == @(-d|--tcdir) ]]; then
            local index=$(($index + 1))
            local tcdirs_additional="${tcdirs_additional} -d ${words[$index]}"
        elif [[ "$current_word" == "--confdir" ]]; then
            local index=$(($index + 1))
            local confdir=${words[$index]}
        elif [[ "$current_word" == "--labconfdir" ]]; then
            local index=$(($index + 1))
            local labconfdir=${words[$index]}
        elif [[ "$current_word" == "--boardconfdir" ]]; then
            local index=$(($index + 1))
            local boardconfdir=${words[$index]}
        elif [[ "$current_word" == @(-c|-p|-l|--config|--logfile|--param) ]]; then
            local index=$(($index + 1))
            if [[ "${words[$(($index + 1))]}" == "=" ]]; then
                local index=$(($index + 2))
            fi
        fi
        local index=$(($index + 1))
    done

    local confdir="${confdir:-config}"
    # Expand path
    eval confdir="${confdir}" 2>/dev/null

    local labconfdir="${labconfdir:-${confdir}/labs}"
    local boardconfdir="${boardconfdir:-${confdir}/boards}"

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '-h -c -p -d -l -v -q -i
            --help --config --param --confdir --labconfdir
            --boardconfdir --tcdir --logfile --verbose
            --quiet --interactive --list-testcases --list-labs
            --list-boards -vv -vvv -vvvv -qq -qqq -qqqq' -- "$cur" ) )
    else
        case $current_mode in
            1)  # LAB
                if [ ! -d $labconfdir ]; then
                    echo
                    echo "Warning: $labconfdir does not exist!"
                    echo -n "${words[@]}"
                    return
                fi
                local labs=$(/bin/ls $labconfdir | grep \\.py | sed 's/\.py$//')
                COMPREPLY=( $( compgen -W "$labs" -- "$cur") )
                ;;
            2)  # BOARD
                if [ ! -d $boardconfdir ]; then
                    echo
                    echo "Warning: $boardconfdir does not exist!"
                    echo -n "${words[@]}"
                    return
                fi
                local boards=$(/bin/ls $boardconfdir | grep \\.py | sed 's/\.py$//')
                COMPREPLY=( $( compgen -W "$boards" -- "$cur") )
                ;;
            *)  # TESTCASE
                # Collecting testcases can be really slow, so we cache them for
                # a small amount of time (10 seconds)
                local cache_age=$(($(date +%s) - ${__tbot_testcase_cache_time:-0}))
                if [[ -z $__tbot_testcase_cache || $cache_age -gt 10 ]]; then
                    __tbot_testcase_cache=$(tbot none none --list-testcases ${tcdirs_additional})
                    __tbot_testcase_cache_time=$(date +%s)
                fi
                COMPREPLY=( $( compgen -W "$__tbot_testcase_cache" -- "$cur") )
                ;;
        esac
    fi
} &&
complete -F _tbot tbot

_tbot-mgr()
{
    local cur prev words cword
    _init_completion || return

    # Completions for subcommands
    local index=0
    local subcommand=""
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" == -* ]]; then
            local index=$(($index + 1))
            continue
        fi

        case "$current_word" in
            "new")
                local subcommand="new"
                _filedir
                return
                ;;
            "init")
                local subcommand="init"
                return
                ;;
            "add")
                local subcommand="add"
                if [[ "$prev" == "add" ]]; then
                    COMPREPLY=( $( compgen -W 'board dummy-board
                        lab dummy-lab dummies' -- "$cur" ) )
                    return
                else
                    local index=$(($index + 1))
                    local current_word="${words[$index]}"

                    case "$current_word" in
                        "board")
                            local subcommand="add-board"
                            [[ "$cur" == -* ]] && \
                                COMPREPLY=( $( compgen -W '-h -s -f -n
                                -l -d -t -0 -1 -c --help --no-interactive
                                --script-mode --force --name --lab
                                --default-lab --toolchain --on --off
                                --connect' -- "$cur" ) ) && \
                            return
                            ;;
                        "lab")
                            local subcommand="add-lab"
                            [[ "$cur" == -* ]] && \
                                COMPREPLY=( $( compgen -W '-h -s -f -n
                                -u -p -k -w --help --no-interactive
                                --script-mode --force --name --user
                                --password --keyfile --workdir' -- "$cur" ) ) && \
                            return
                            ;;
                        "dummy-board")
                            local subcommand="add-dummy-board"
                            [[ "$cur" == -* ]] && \
                                COMPREPLY=( $( compgen -W '-h -s -f -n
                                -l --help --no-interactive
                                --script-mode --force --name --lab' -- "$cur" ) ) && \
                            return
                            ;;
                        "dummy-lab")
                            local subcommand="add-dummy-lab"
                            [[ "$cur" == -* ]] && \
                                COMPREPLY=( $( compgen -W '-h -s -f -n
                                --help --no-interactive --script-mode
                                --force --name' -- "$cur" ) ) && \
                            return
                            ;;
                        "dummies")
                            local subcommand="add-dummy-both"
                            [[ "$cur" == -* ]] && \
                                COMPREPLY=( $( compgen -W '-h -s -f -n
                                --help --no-interactive --script-mode
                                --force --name' -- "$cur" ) ) && \
                            return
                            ;;
                    esac
                fi
        esac

        local index=$(($index + 1))
    done

    # Completions for flags
    case "$prev" in
        "-k"|"--keyfile")
            _filedir
            return
            ;;
        "-w"|"--workdir")
            _filedir
            return
            ;;
        "-l"|"--lab")
            local labs=$(/bin/ls $labconfdir | grep \\.py | sed 's/\.py$//')
            COMPREPLY=( $( compgen -W "$labs" -- "$cur") )
            return
            ;;
        -*)
            return
            ;;
    esac

    # Other completions
    if [[ $subcommand == "add-lab" ]]; then
        _known_hosts
        return
    fi

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '-h --help' -- "$cur" ) )
    else
        COMPREPLY=( $( compgen -W 'new init add' -- "$cur" ) )
    fi
} &&
complete -F _tbot-mgr tbot-mgr

#ex: filetype=sh
