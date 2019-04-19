#!/usr/bin/python

import sys
import os
import subprocess


class SubGit(object):
    def __init__(self, f):
        self.subs = {}

        with open(f) as fp: 
            current = None
            for l in fp:
                l = l.strip()
                if not l:
                    continue
                if l[0] == '[' and l[-1] == ']':
                    current = {}
                    self.subs[l[1:-1]] = current
                    continue

                if ':' in l:
                    parts = l.split(":")
                    key= parts[0].strip()
                    val = ":".join(parts[1:]).strip()
                    current[key] = val

    def dirs(self):
        return self.subs.iteritems()

def do_status(args):
    "Show git-status of each repo listed in .subgit"
    subgit = SubGit(".subgit")

    cmd = ["git", "status", "--porcelain=v1", "-b"]
    for path, infos in subgit.dirs():
        if not os.path.isdir(path):
            print "WARNING: no such dir: {}\n".format(path)
            continue
        run = subprocess.Popen(cmd, cwd=path, stdout = subprocess.PIPE)
        stdout, stderr = run.communicate()

        print "[{}]".format(path)
        for line in stdout.split("\n"):
            if not line:
                continue
            print line
        print


def run_status(subgit):
    for path, infos in subgit.dirs():
        cmd = ["git", "status"]
        print "{}:: {}".format(path, " ".join(cmd))
        subprocess.check_output(cmd, cwd=path)



def do_checkout(args):
    "Perform clone and checkout of each repo listed in .subgit"
    subgit = SubGit(".subgit")
    run_clone(subgit)
    run_checkout(subgit)

def do_update(args):
    "Perform fetch and update of each repo listed in .subgit. Pass 'dev' to checkout tip"
    co_master = 'dev' in args
    subgit = SubGit(".subgit")
    run_fetch(subgit)
    run_checkout(subgit, co_master)

def do_clone(args):
    "Perform clone and checkout of each repo in .subgit. Possibly duplicates checkout!?"
    subgit = SubGit(".subgit")
    for d,info in subgit.dirs():
        if os.path.isdir(d):
            print "{} : already exists".format(d)
            continue

        uri = info['uri']
        branch = info['branch']

        if uri == '<NO URI>':
            print "Not cloning local {}.".format(d)
            continue

        cmd = ["git", "clone", "-n", "-b", branch, uri, d]
        print "{}".format(" ".join(cmd))
        subprocess.check_output(cmd)

        if 'dev' in args:
            rev = 'master'
        else:
            rev = info['commit']

        cmd = ["git", "checkout", rev]
        print "{}".format(" ".join(cmd))
        subprocess.check_output(cmd, cwd=d)




def find_repos(include_root=False):
    repodirs = []
    for subdir, dirs, files in os.walk("."):
        if ".git" in dirs and (subdir != "." or include_root):
            repodirs.append(os.path.relpath(subdir))
    return repodirs

def get_dir_status(d):
    s = {}
    cmd = ['git', 'status', '--porcelain=v2', '-b']
    lines = subprocess.check_output(cmd, cwd=d)

    try:
        print "getting status of ", d
        uri = subprocess.check_output(['git', 'remote', 'get-url', 'origin'],cwd=d)
        print "got"
        s['uri'] = uri.strip()
    except subprocess.CalledProcessError:
        print "WHOOPS"
        s['uri'] = '<NO URI>'

    changes = []

    for l in lines.split('\n'):
        if l.startswith('# branch.oid'):
            s['commit'] =  l.split()[2]
        elif l.startswith('# branch.head'):
            s['branch'] =  l.split()[2]
        elif l.startswith('# branch.ab'):
            s['ahead'] =  int(l.split()[2])
        elif l.startswith('1 .M'):
            changes.append(l.split(' ')[-1])

    s['changes'] = changes


    show_fmt = 'author : %an <%ae>%ntime : %aI%nsummary : %s'
    cmd = ['git', 'show', s['commit'], '-s', '--pretty=format:{}'.format(show_fmt)]
    try:
        lines = subprocess.check_output(cmd, cwd=d)
        for l in lines.split('\n'):
            k,v = l.split(' : ')
            s[k] = v
    except subprocess.CalledProcessError:
        #print subprocess.CalledProcessError
        pass

    return s

def do_push(args):
    "Push all repos that have outstanding commits"

    statii = dict([ (d,get_dir_status(d)) for d in find_repos()])
    cmd = ['git', 'push', '--porcelain' ]
    print "\n\nGOT STATUS\n\n"

    for d, info in statii.items():
        if info.get('ahead',0) != 0:
            print "WOULD PUSH: {} has {} ".format(d, info['ahead'])
            lines = subprocess.check_output(cmd, cwd=d)
            print lines
        else:
            print "No need to push {}".format(d)
        print


def do_refresh(args):
    "Write .subgit file with info of each found git subrepo"
    cmd = ['git', 'status', '--porcelain=v2', '-b']
    statii = dict([ (d,get_dir_status(d)) for d in find_repos()])

    with open(".subgit", "w") as fp:
        for d, info in statii.items():
            if info.get('ahead',0) != 0:
                print "Warning: {} has {} unpushed commits".format(d,
                        info['ahead'])
            if info['changes'] != []:
                print "Warning: {} has {} uncommitted changes:".format(d,
                        len(info['changes']))
                for f in info['changes']:
                    print "  ", f
            reldir = os.path.relpath(d)
            fp.write("[{}]\n".format(reldir))
            for k,v in info.items():
                if k == 'changes': continue
                if k == 'ahead': continue
                fp.write("{} : {}\n".format(k,v))
            fp.write("\n")


def run_checkout(subgit, co_master=False):
    for path, infos in subgit.dirs():
        if co_master:
            rev = 'master'
        else:
            rev = infos['commit']

        if not os.path.isdir(path):
            if infos['uri'] == '<NO URI>':
                print "Skipping local {}".format(path)
                continue
            else:
                raise "Can't fetch: no such dir: {}".format(
                        path)

        cmd = ["git", "checkout", rev]
        subprocess.check_output(cmd, cwd=path)

        if co_master:
            cmd = ["git", "pull"]
            print "{}".format(" ".join(cmd))
            subprocess.check_output(cmd, cwd=path)
        print

def run_fetch(subgit):
    for path, infos in subgit.dirs():
        if not os.path.isdir(path):
            if infos['uri'] == '<NO URI>':
                print "Skipping local {}".format(path)
                continue
            else:
                raise "Can't fetch: no such dir: {}".format(
                        path)
        cmd = ["git", "fetch", "-vvvv"]
        print "{}".format(" ".join(cmd))
        subprocess.check_output(cmd, cwd=path)
        print

def run_clone(subgit):
    for path, infos in subgit.dirs():
        uri = infos['uri']
        branch = infos['branch']

        cmd = ["git", "clone", "-n", "-b", branch, uri, path]
        print "{}".format(" ".join(cmd))
        subprocess.check_output(cmd)
        print




def main(args):

    cmds = {
        "checkout" : do_checkout,
        "update"   : do_update,
        "status"   : do_status,
        "refresh"  : do_refresh,
        "clone"    : do_clone,
        "push"     : do_push,
    }

    if len(args) == 1:
        print "Available commands:"
        maxlen =  max([len(x) for x in cmds.keys()]) + 1
        for k,v in cmds.items():
            space = " " *  (maxlen - len(k))
            d = v.func_doc if v.func_doc else ""
            print "  {}{}: {}".format(k,space,d)
        return 1

    def nosuch(args):
        print "No such command: {}".format(args)
        return 1

    cmd = cmds.get(args[1], nosuch)
    return cmd(args[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))



