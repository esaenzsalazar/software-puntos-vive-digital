"""
Script de prueba para verificar que todas las páginas del sistema PVD funcionan correctamente.
Ejecutar con: python test_pages.py
"""
import http.client
import sys

BASE_URL = "127.0.0.1:8000"

# Páginas que requieren autenticación (esperan 302 redirect to login)
AUTH_REQUIRED = [
    "/panel/",
    "/pvd/",
    "/pvd/crear/",
    "/crear-admin-tic/",
    "/crear-admin-pvd/",
    "/gestionar-roles/",
    "/consultar-ciudadanos/",
    "/registrar-ciudadano/",
    "/reportes/",
    "/salas/",
    "/perfil/",
]

# Páginas públicas (esperan 200)
PUBLIC_PAGES = [
    "/login/",
    "/registrar-usuario-ciudadano/",
]

def test_page(url, expected_status):
    """Test a single page."""
    try:
        conn = http.client.HTTPConnection(BASE_URL, timeout=5)
        conn.request("GET", url)
        response = conn.getresponse()
        status = response.status
        
        if status == expected_status or (expected_status == 302 and status in [301, 302, 303]):
            print(f"✅ {url} - Status: {status}")
            return True
        else:
            print(f"❌ {url} - Expected: {expected_status}, Got: {status}")
            return False
    except Exception as e:
        print(f"❌ {url} - ERROR: {e}")
        return False
    finally:
        conn.close()

def main():
    """Run all tests."""
    print("=" * 60)
    print("PRUEBA DE PÁGINAS - PUNTOS VIVE DIGITAL")
    print("=" * 60)
    
    all_passed = True
    
    print("\n📝 Páginas públicas (esperado: 200 OK):")
    for url in PUBLIC_PAGES:
        if not test_page(url, 200):
            all_passed = False
    
    print("\n🔒 Páginas con autenticación (esperado: 302 Redirect to login):")
    for url in AUTH_REQUIRED:
        if not test_page(url, 302):
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
        return 0
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
