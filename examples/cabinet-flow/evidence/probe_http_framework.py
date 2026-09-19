"""Bounded framework experiment, not a Cabinet Flow implementation or emitter.

Run with the project's already-installed FastAPI/Starlette environment. This
proves direct handler registration and Response/error semantics only.
"""
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import FastAPIError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


def probe() -> dict:
    project = Path(__file__).resolve().parents[1]
    routes = json.loads((project / '70_router_closure.json').read_text())['items']
    contracts = json.loads((project / '60_contracts.json').read_text())['contracts']
    checks = []
    # The earlier non-serializable context cannot be inferred as an HTTP body.
    class OpaqueContext:
        pass

    async def old_shape(context: OpaqueContext) -> Response:
        return Response()

    try:
        FastAPI().add_api_route('/old', old_shape, methods=['POST'])
    except FastAPIError:
        checks.append('opaque_context_is_not_a_registerable_body_parameter')
    else:
        raise AssertionError('Framework unexpectedly accepted the opaque context')

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    observed = []

    def endpoint(name):
        async def handler(request: Request) -> Response:
            assert isinstance(request, Request)
            raw = await request.body()
            observed.append((name, raw))
            if raw == b'raise-probe-error':
                raise RuntimeError('SENTINEL_NOT_FOR_RESPONSE')
            return JSONResponse({'probe_handler': name}, status_code=202)
        handler.__name__ = name
        return handler

    async def safe_error(request: Request, error: Exception) -> Response:
        status = error.status_code if isinstance(error, HTTPException) else 500
        return JSONResponse({'status_code': status, 'result': None,
                             'error_code': 'probe_failure',
                             'error_message': 'Fixed probe message.'},
                            status_code=status)

    app.add_exception_handler(HTTPException, safe_error)
    app.add_exception_handler(Exception, safe_error)
    for row in routes:
        assert contracts[row['handler']] == '(request: Request) -> Response'
        app.add_api_route(row['path'], endpoint(row['handler']), methods=[row['method']])
    with TestClient(app, raise_server_exceptions=False) as client:
        for row in routes:
            response = client.post(row['path'], json={'probe': True})
            assert response.status_code == 202
            assert response.json() == {'probe_handler': row['handler']}
        assert len(observed) == len(routes) == 6
        checks.append('all_six_request_only_handlers_register_and_receive_request')
        checks.append('direct_response_preserves_status_and_body')
        assert len(app.routes) == 6
        checks.append('no_implicit_documentation_routes')
        for method, path, body, expected in [
            ('GET', routes[0]['path'], None, 405),
            ('POST', '/absent', None, 404),
            ('POST', routes[0]['path'], b'raise-probe-error', 500),
        ]:
            response = client.request(method, path, content=body)
            assert response.status_code == expected
            assert response.json()['status_code'] == expected
            assert 'SENTINEL' not in response.text
        checks.append('404_405_500_support_bounded_custom_envelope')
    return {'result': 'PASS', 'verified_at': datetime.now(timezone.utc).isoformat(),
            'versions': {p: version(p) for p in ('fastapi', 'starlette', 'pydantic', 'httpx')},
            'checks': checks,
            'scope': 'Framework semantics only; no product, authentication, TLS or Factory emission claim.'}


if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
