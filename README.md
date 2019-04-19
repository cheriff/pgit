# pgit
Python wrapper of git for sub-repos

#### Note:
Seems unhappy with old git `git version 2.6.4 (Apple Git-63)` - try updating

## What
Maintains a list of secondary git trees in a file named .subgit, which typicially is checked in with the parent project.
This allows locking in a specific checkin of each dependancy. As subtrees are updated (whether by tracking an upstream or new development) the file may be refreshed and checked in.

## Why

For reasons I can't remember, I was never truly happy with existing git + submodule support.
So I ended up accidentally writing a new one.

## How
Run the script, specifying a sub-command.

### Subcommands
The available subcommands are:

#### Status
Shows the current status of each git subtree

#### Checkout
Clones each each git subtree from their respective upstreams, and checks out the listed revision.

#### Update
Performs `git fetch` on each subtree and updates to the listed revision. 
If `dev` is passed as an argument, then the repo's tip is used instead. If this works nicely then `refresh` may be subsequently used.

#### Refresh
Writes a new .subgit file with info of each found git subtree. 

Subtrees are found by searching for their `.git` directories, so manually cloning something and then running `./pgit refresh` will be sufficient.

If existing subtrees are now on a differnt revision (i.e new commits or tracking upstream) then this will be recorded in .subgit

#### Clone
Perform clone and checkout of each repo in .subgit. Might actually be an smarter alias of `checkout`?

#### Push
If changes are present in subtrees, push them.
