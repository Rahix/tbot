_tbot()
{
    local cur prev words cword
    _init_completion || return

    # Collect testcase path arguments
    local index=0
    local path_args=()
    local curdir="$(pwd)"
    local workdir="${curdir}"
    while [[ $index -lt ${#words[@]} ]]; do
        local current_word="${words[$index]}"

        if [[ "$current_word" == @(-T|-t) ]]; then
            local index=$(($index + 1))
            path_args=("${path_args[@]}" "$current_word" "${words[$index]}")
        elif [[ "$current_word" == -C ]]; then
            local index=$(($index + 1))
            path_args=("${path_args[@]}" "$current_word" "${words[$index]}")
            workdir="${words[$index]}"
        fi

        local index=$(($index + 1))
    done

    if [[ "$prev" == -C ]]; then
        _filedir -d
        return
    fi

    if [[ "$prev" == -T ]]; then
        cd "${workdir}" && _filedir -d
        cd "${curdir}"
        return
    fi

    if [[ "$prev" == @(-t|-b|-l|--board|--lab) ]]; then
        cd "${workdir}" && _filedir py
        cd "${curdir}"
        # Remove __pycache__ for convenience
        COMPREPLY=("${COMPREPLY[@]/*__pycache__*/}")
        return
    fi

    if [[ "$prev" == "--log" ]]; then
        cd "${workdir}" && _filedir
        cd "${curdir}"
        return
    fi

    if [[ "$prev" == @(-f) ]]; then
        COMPREPLY=()
        return
    fi

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '-h -b -l -T -t -f -v -q -s -i -C -p
            --help
            --board
            --lab
            --log
            --log-auto
            --version
            --list-testcases
            --list-files
            --list-flags
            --show
            --interactive
        ' -- "$cur" ) )
    else
        # Collecting testcases can be really slow, so we cache them for
        # a small amount of time (5 seconds)
        local cache_age=$(($(date +%s) - ${__tbot_testcase_cache_time:-0}))
        if [[ -z $__tbot_testcase_cache || $cache_age -gt 5 ]]; then
            __tbot_testcase_cache=$(tbot --list-testcases "${path_args[@]}" 2>/dev/null)
            __tbot_testcase_cache_time=$(date +%s)
        fi
        COMPREPLY=( $( compgen -W "$__tbot_testcase_cache" -- "$cur") )
    fi
} &&
complete -F _tbot tbot
