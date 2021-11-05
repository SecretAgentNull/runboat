import datetime

from runboat.db import BuildsDb
from runboat.models import Build, BuildInitStatus, BuildStatus


def _make_build(
    name: str | None = None,
    *,
    status: BuildStatus | None = None,
    init_status: BuildInitStatus | None = None,
    repo: str | None = None,
    pr: int | None = None,
) -> Build:
    name = name or "build-a"
    return Build(
        name=name,
        deployment_name=name + "-odoo",
        repo=repo or "oca/mis-builder",
        target_branch="15.0",
        pr=pr or None,
        git_commit="0d35a10f161b410f2baa3d416a338d191b6dabc0",
        image="ghcr.io/oca/oca-ci:py3.8-odoo15.0",
        status=status or BuildStatus.starting,
        init_status=init_status or BuildInitStatus.todo,
        desired_replicas=0,
        last_scaled=datetime.datetime(2021, 10, 1, 12, 0, 0),
        created=datetime.datetime(2021, 10, 1, 11, 0, 0),
    )


def test_add():
    db = BuildsDb()
    assert db.add(_make_build())  # new
    assert not db.add(_make_build())  # no change
    assert db.add(_make_build(status=BuildStatus.failed))


def test_remove():
    db = BuildsDb()
    assert not db.remove("not-a-build")
    build = _make_build()
    db.add(build)
    assert db.remove(build.name)


def test_get_for_commit():
    db = BuildsDb()
    build = _make_build()
    db.add(build)
    assert (
        db.get_for_commit(
            build.repo, build.target_branch, build.pr, git_commit=build.git_commit
        )
        == build
    )
    assert (
        db.get_for_commit(
            "not-a-build", build.target_branch, build.pr, git_commit=build.git_commit
        )
        is None
    )


def test_search():
    db = BuildsDb()
    db.add(build1 := _make_build(name="b1", repo="oca/repo1"))
    db.add(_make_build(name="b2", repo="oca/repo2"))
    assert len(db.search()) == 2
    assert db.search("oca/repo1") == [build1]


def test_count_by_status():
    db = BuildsDb()
    db.add(_make_build(name="b1", status=BuildStatus.started))
    db.add(_make_build(name="b2", status=BuildStatus.stopped))
    assert db.count_by_status(BuildStatus.started) == 1
    assert db.count_by_status(BuildStatus.stopped) == 1
    assert db.count_by_status(BuildStatus.failed) == 0


def test_count_by_init_status():
    db = BuildsDb()
    db.add(_make_build(name="b1", init_status=BuildInitStatus.started))
    db.add(_make_build(name="b2", init_status=BuildInitStatus.todo))
    assert db.count_by_init_status(BuildInitStatus.started) == 1
    assert db.count_by_init_status(BuildInitStatus.todo) == 1
    assert db.count_by_init_status(BuildInitStatus.failed) == 0


def test_count_all():
    db = BuildsDb()
    assert db.count_all() == 0
    db.add(_make_build(name="b1"))
    assert db.count_all() == 1
    db.add(_make_build(name="b2"))
    assert db.count_all() == 2
