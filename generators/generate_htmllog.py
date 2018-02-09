#!/usr/bin/python3
"""
Generate an html log
--------------------
Create an html representation of the log,
using U-Boot's python test suite's html log
generator as a base
"""
import json

def main():
    """ Generate an html log """

    log = json.load(open("log.json"))

    #pylint: disable=too-many-return-statements
    def gen_html(msg):
        """ Generate html for a log message """
        if msg['type'] == ["testcase", "begin"]:
            return f"""<div class="section block">
                         <div class="section-header block-header">
                           {msg['name']}
                         </div>
                         <div class="section-content block-content">
                           <div class="action">
                             <pre></pre>
                           </div>"""
        elif msg['type'] == ["testcase", "end"]:
            return f"""    <div class="status-pass">
                             <pre>OK, Time: {msg['duration']:.2f}s</pre>
                           </div>
                         </div>
                       </div>"""
        elif msg['type'][0] == "shell":
            shell_type = repr(tuple(msg['type'][1:]))
            command = repr(msg['command'])[1:-1]
            output = msg['output'][:-1].replace('<', '&lt;') \
                .replace('>', '&gt;') \
                .replace('&', '&amp;')
            return f"""    <div class="stream block">
                             <div class="stream-header block-header">
                               {shell_type} {command}
                             </div>
                             <div class="stream-content block-content">
                               <pre>
{output}</pre>
                             </div>
                           </div>"""
        elif msg['type'] == ["board", "boot"]:
            return f"""    <div class="stream block">
                             <div class="stream-header block-header">
                               -&gt; Board boot log
                             </div>
                             <div class="stream-content block-content">
                               <pre>
{msg['log']}</pre>
                             </div>
                           </div>"""
        elif msg['type'] == ["msg"]:
            return f"""    <div class="stream block">
                             <div class="stream-header block-header">
                               Message:
                             </div>
                             <div class="stream-content block-content">
                               <pre>
{msg['text']}</pre>
                             </div>
                           </div>"""
        elif msg['type'] == ["boardshell_cleanup"] \
             or msg['type'] == ["tbotend"] \
             or msg['type'][0] == "custom" \
             or msg['type'][0] == "doc":
            return ""

        raise Exception("unknown event %r" % (msg,))

    # Header
    print("""<html>
<head>
<link rel="stylesheet" type="text/css" href="multiplexed_log.css">
<script src="http://code.jquery.com/jquery.min.js"></script>
<script>
$(document).ready(function () {
    // Add expand/contract buttons to all block headers
    btns = "<span class=\\"block-expand hidden\\">[+] </span>" +
        "<span class=\\"block-contract\\">[-] </span>";
    $(".block-header").prepend(btns);

    // Add expand/contract buttons to all block headers dir
    btnsd = "<span class=\\"block-expand hidden\\">[+] </span>" +
        "<span class=\\"block-contract\\">[-] </span>";
    $(".block-header-dir").prepend(btns);

    // Pre-contract all blocks which passed, leaving only problem cases
    // expanded, to highlight issues the user should look at.
    // Only top-level blocks (sections) should have any status
    passed_bcs = $(".block-content:has(.status-pass)");
    // Some blocks might have multiple status entries (e.g. the status
    // report), so take care not to hide blocks with partial success.
    passed_bcs = passed_bcs.not(":has(.status-fail)");
    passed_bcs = passed_bcs.not(":has(.status-xfail)");
    passed_bcs = passed_bcs.not(":has(.status-xpass)");
    passed_bcs = passed_bcs.not(":has(.status-skipped)");
    // Expand top level
    passed_bcs = passed_bcs.not("tt > div > div");
    // Hide the passed blocks
    passed_bcs.addClass("hidden");
    // Flip the expand/contract button hiding for those blocks.
    bhs = passed_bcs.parent().children(".block-header")
    bhs.children(".block-expand").removeClass("hidden");
    bhs.children(".block-contract").addClass("hidden");

    // Flip the expand/contract button hiding for those blocks.
    bhsd = passed_bcs.parent().children(".block-header-dir")
    bhsd.children(".block-expand").removeClass("hidden");
    bhsd.children(".block-contract").addClass("hidden");

    // Add click handler to block headers.
    // The handler expands/contracts the block.
    $(".block-header").on("click", function (e) {
        var header = $(this);
        var content = header.next(".block-content");
        var expanded = !content.hasClass("hidden");
        if (expanded) {
            content.addClass("hidden");
            header.children(".block-expand").first().removeClass("hidden");
            header.children(".block-contract").first().addClass("hidden");
        } else {
            header.children(".block-contract").first().removeClass("hidden");
            header.children(".block-expand").first().addClass("hidden");
            content.removeClass("hidden");
        }
    });

    // Add click handler to block headers dir.
    // The handler expands/contracts the block.
    $(".block-header-dir").on("click", function (e) {
        var header = $(this);
        var content = header.next(".block-content");
        var expanded = !content.hasClass("hidden");
        if (expanded) {
            content.addClass("hidden");
            header.children(".block-expand").first().removeClass("hidden");
            header.children(".block-contract").first().addClass("hidden");
        } else {
            header.children(".block-contract").first().removeClass("hidden");
            header.children(".block-expand").first().addClass("hidden");
            content.removeClass("hidden");
        }
    });

    // When clicking on a link, expand the target block
    $("a").on("click", function (e) {
        var block = $($(this).attr("href"));
        var header = block.children(".block-header");
        var content = block.children(".block-content").first();
        header.children(".block-contract").first().removeClass("hidden");
        header.children(".block-expand").first().addClass("hidden");
        content.removeClass("hidden");
    });
});
</script>
</head>
<body>
<tt>
""")

    print("\n".join(map(gen_html, log)))

    # Footer
    print("""</tt>
</body>
</html>""")

if __name__ == "__main__":
    main()
