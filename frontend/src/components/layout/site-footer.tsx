export function SiteFooter() {
  return (
    <footer className="bg-primary text-white mt-16">
      <div className="container-site py-10 grid gap-6 md:grid-cols-3">
        <div>
          <p className="font-display text-2xl uppercase">CUEP</p>
          <p className="text-sm mt-2">Colectivo Universitario por la Educación Popular</p>
        </div>
        <div className="text-sm space-y-2">
          <p className="font-semibold">Navegación</p>
          <p>Login</p>
          <p>Registro</p>
          <p>Convocatorias</p>
        </div>
        <div className="text-sm space-y-2">
          <p className="font-semibold">Contacto</p>
          <p>educacionpopular@cuep.org</p>
          <p>Redes sociales del colectivo</p>
        </div>
      </div>
    </footer>
  );
}
