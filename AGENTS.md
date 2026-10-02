# Testing rule changes on real projects

Unit tests are not enough to validate a rule change. Before you consider done
any change to a rule (a new rule, a change to an existing rule, a new fix, or a
change to an existing fix), test it against these projects, at these commits:

| Project | Commit | Scrapy project root |
|---|---|---|
| [alltheplaces](https://github.com/alltheplaces/alltheplaces) | `dd9b5f8da34afb8969cfc48812309b052d886915` | `.` |
| [querido-diario](https://github.com/okfn-brasil/querido-diario) | `c865658114970927df95ce3baa7ae99e833a2ab4` | `querido_diario_raspadores` |
| [kingfisher-collect](https://github.com/open-contracting/kingfisher-collect) | `8d9aec39893498d2e0b80039404b7cefeede7795` | `.` |
| [city-scrapers](https://github.com/City-Bureau/city-scrapers) | `0a9a9fbbf894d9c6b802df50500e9c8e6f5fa086` | `.` |

Some of these projects use scrapy-lint, or are about to, which hides reports in
later commits, so keep the pins.

1. Shallow-clone each project at its commit into a temporary directory outside
   this repository, run `scrapy-lint` in its Scrapy project root, once from
   your branch and once from `origin/master`, and diff the two outputs:

   ```bash
   REPO=$PWD WORK=$(mktemp -d)
   git worktree add --detach $WORK/master origin/master
   while read -r name url commit root; do
       git init -q $WORK/$name
       git -C $WORK/$name fetch -q --depth 1 $url $commit
       git -C $WORK/$name checkout -q FETCH_HEAD
       (
           cd $WORK/$name/$root
           uv run --project $WORK/master scrapy-lint > $WORK/$name.before.txt
           uv run --project $REPO scrapy-lint > $WORK/$name.after.txt
       )
       diff $WORK/$name.before.txt $WORK/$name.after.txt
   done <<'EOF'
   alltheplaces https://github.com/alltheplaces/alltheplaces dd9b5f8da34afb8969cfc48812309b052d886915 .
   querido-diario https://github.com/okfn-brasil/querido-diario c865658114970927df95ce3baa7ae99e833a2ab4 querido_diario_raspadores
   kingfisher-collect https://github.com/open-contracting/kingfisher-collect 8d9aec39893498d2e0b80039404b7cefeede7795 .
   city-scrapers https://github.com/City-Bureau/city-scrapers 0a9a9fbbf894d9c6b802df50500e9c8e6f5fa086 .
   EOF
   git -C $REPO worktree remove $WORK/master
   ```

2. Check every issue that appears or disappears for the rules your change
   touches, and confirm that each one is a real issue, or a real fix of a
   misreport. For a new rule with many reports, classify all of them, e.g.
   with an AST script, and inspect examples of every bucket.

3. For fix changes, run `scrapy-lint --fix` on a copy of each clone, then check
   that the changed files compile, that each edit is equivalent to the
   original code, and that a new `scrapy-lint` run reports no new issues.
   Where possible, also run the project's own tests and `scrapy list` on the
   fixed copy.

4. Summarize the results in the pull request description: counts per project
   and rule before and after, and any report you consider debatable, with your
   reasons.

5. Turn every misreport you find this way into a test case in this
   repository.

Never commit to those clones, and never push anything to those projects.
