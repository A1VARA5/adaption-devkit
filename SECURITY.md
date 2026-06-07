# Security policy

adaption-devkit is a community, unofficial, open source project. It is not
affiliated with or endorsed by Adaption Labs. This policy covers the toolkit in
this repository only.

## Reporting a concern in this toolkit

If you find a security concern in adaption-devkit, please report it privately
rather than opening a public issue.

- Open a private report through GitHub's security advisory feature on this
  repository, or
- Contact the maintainer, Aivaras Navardauskas, on GitHub
  [A1VARA5](https://github.com/A1VARA5).

Please give enough detail to reproduce the concern. We will acknowledge your
report and work with you on a fix before any public disclosure.

## This is not the place for Adaption platform issues

This policy is for the code in this repository. It is not a channel for reporting
security issues in the Adaption platform, the Adaptive Data service, or the
official `adaption` SDK. For anything about the platform itself, use Adaption's
own official channels; their documentation is the source of truth.

## Never commit API keys

Treat your Adaption API key, and any other credential, as a secret.

- Never commit an API key, a base URL with a key in it, or any credential to
  source control. Never paste one into a notebook you plan to share.
- Keep keys in environment variables, for example `ADAPTION_API_KEY` and
  `ADAPTION_BASE_URL`, or in a local `.env` file that git ignores.
- The tools in this kit read keys only from the environment. They do not store
  keys, and they will never ask you to hardcode one.

If a key is ever exposed, rotate it immediately through your Adaption account,
then scrub it from any history that captured it.
