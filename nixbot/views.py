from pyramid.view import view_config

from .hydra_jobsets import HydraJobsets
from .pr_merge import merge_push

HELP = """
Hi! I'm a bot that helps with reviewing and testing Nix code.

Commands:

- `@{bot_name} build` creates a new Hydra jobset and reports results
"""


@view_config(
    route_name='github-webhook',
    renderer='json',
)
def github_webhook(request):
    """
    https://developer.github.com/webhooks/

    TODO: use secret authenticate github using X-Hub-Signature
    """
    event = request.headers['X-GitHub-Event']
    print(event)
    payload = request.json_body
    bot_name = request.registry.settings['nixbot.bot_name']

    if event == "pull_request":
        if payload.get("action") in ["opened", "reopened", "edited"]:
            pr = request.registry.gh.pull_request(
                payload["pull_request"]["base"]["repo"]["owner"]["login"],
                payload["pull_request"]["base"]["repo"]["name"],
                payload["pull_request"]["number"]
            )
            # TODO: evaluate and report statistics
            pr.create_comment(HELP.format(bot_name=bot_name))
    elif event == "issue_comment":
        if payload.get("action") in ["created", "edited"]:
            comment = payload['comment']['body'].strip()
            bot_prefix = '@{} '.format(bot_name)
            # TODO: support merge
            if comment == (bot_prefix + "build"):
                # TODO: this should ignore issues
                pr = request.registry.gh.pull_request(
                    payload["repository"]["owner"]["login"],
                    payload["repository"]["name"],
                    payload["issue"]["number"]
                )
                if request.registry.repo.is_collaborator(payload["comment"]["user"]["login"]):
                    jobset = test_github_pr(
                        payload["issue"]["number"],
                        request.registry.settings,
                        # TODO support specifying base
                        pr.base.ref
                    )
                    pr.create_comment("Jobset created at {}".format(jobset))
                else:
                    pr.create_comment("@{} is not a committer".format(payload["comment"]["user"]["login"]))

    return "Done"


def test_github_pr(pr_id, settings, base):
    jobsets = HydraJobsets(settings)
    jobsets.add(pr_id)
    merge_push(pr_id, base, settings)

    return "XXXurl"
