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
        # Remove __pycache__ for convenience
        COMPREPLY=(${COMPREPLY[@]/*__pycache__*/})
        return
    fi

    if [[ "$prev" == @(-f) ]]; then
        COMPREPLY=()
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
        COMPREPLY=( $( compgen -W '-h -b -l -T -t -s -i -f
            --list-testcases --list-boards --list-labs --list-files
            --list-flags --board --lab --show --interactive' -- "$cur" ) )
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
