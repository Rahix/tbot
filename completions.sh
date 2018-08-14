_tbot()
{
    local cur prev words cword
    _init_completion || return

    if [[ "$prev" == -T ]]; then
        _filedir -d
        return
    fi

    if [[ "$prev" == @(-t|-b|-l|--board|--lab) ]]; then
        _filedir py
        return
    fi

    # Collect testcase path arguments
    local index=0
    local path_args=""
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" == @(-T|-t) ]]; then
            local index=$(($index + 1))
            path_args="$path_args $current_word ${words[$index]}"
        fi

        local index=$(($index + 1))
    done

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '-h -b -l -T -t -s -i
            --list-testcases --list-boards --list-labs --list-files
            --board --lab --show --interactive' -- "$cur" ) )
    else
        # Collecting testcases can be really slow, so we cache them for
        # a small amount of time (5 seconds)
        local cache_age=$(($(date +%s) - ${__tbot_testcase_cache_time:-0}))
        if [[ -z $__tbot_testcase_cache || $cache_age -gt 5 ]]; then
            __tbot_testcase_cache=$(tbot --list-testcases ${path_args} 2>/dev/null)
            __tbot_testcase_cache_time=$(date +%s)
        fi
        COMPREPLY=( $( compgen -W "$__tbot_testcase_cache" -- "$cur") )
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
            "del")
                local subcommand="del"
                if [[ "$prev" == "del" ]]; then
                    COMPREPLY=( $( compgen -W 'board lab' -- "$cur" ) )
                    return
                else
                    local index=$(($index + 1))
                    local current_word="${words[$index]}"

                    case "$current_word" in
                        "board")
                            local subcommand="del-board"
                            local boards=$(/bin/ls config/boards | grep \\.py | sed 's/\.py$//')
                            COMPREPLY=( $( compgen -W "$boards" -- "$cur") )
                            return
                            ;;
                        "lab")
                            local subcommand="del-lab"
                            local labs=$(/bin/ls config/labs | grep \\.py | sed 's/\.py$//')
                            COMPREPLY=( $( compgen -W "$labs" -- "$cur") )
                            return
                            ;;
                    esac
                fi
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
        COMPREPLY=( $( compgen -W 'new init del add' -- "$cur" ) )
    fi
} &&
complete -F _tbot-mgr tbot-mgr

#ex: filetype=sh
