# Function to display full paths to the executable of the running processes.
# Usage:
# $ pexe <cmd>

pexe() {
    pgrep -f "$1" | xargs -d $'\n' sh -c 'for arg do echo -n "$arg "; readlink -f /proc/"$arg"/exe; done' _
}
