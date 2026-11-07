# Security Policy

## About This Project

SecureGate is an educational project demonstrating web application
security concepts. It intentionally includes vulnerable code under
`security/vulnerability-labs/`, isolated and gated for local-only use.

## Scope

This is a student portfolio project, not a production service or a
publicly deployed application. There is no live, hosted instance to
report issues against.

## Responsible Use of the Vulnerability Labs

The applications under `security/vulnerability-labs/` are intentionally
insecure and must only ever be run on `127.0.0.1`. They are gated behind
the `SECUREGATE_LAB=1` environment variable specifically to prevent
accidental exposure. Do not remove this guard, and never deploy these labs
to any shared, public, or production network.

## Reporting a Concern

If you notice an unintended vulnerability in the **secure** application
(i.e., anything outside `security/vulnerability-labs/`) that isn't already
documented in `security/reports/`, please open a GitHub issue describing
the concern. As this is a learning project with no production deployment,
there is no bug bounty or formal disclosure timeline, but feedback is
welcome and appreciated.

## Supported Versions

This project is not actively maintained as a production dependency. The
`v1.0.0` tag represents the completed state of the educational exercise.