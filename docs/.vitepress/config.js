import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/reservas-ia/',
  title: 'GlampBook',
  description: 'Plataforma de reservas para glamping — documentación técnica',
  lang: 'es',
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/reservas-ia/favicon.ico' }],
  ],

  themeConfig: {
    logo: '🏕️',
    siteTitle: 'GlampBook',

    nav: [
      { text: 'Inicio', link: '/' },
      { text: 'Guía rápida', link: '/guia-inicio' },
      { text: 'API', link: '/api' },
      {
        text: 'GitHub',
        link: 'https://github.com/JohnEduar/reservas-ia',
        target: '_blank',
      },
    ],

    sidebar: [
      {
        text: 'Introducción',
        items: [
          { text: '¿Qué es GlampBook?', link: '/' },
          { text: 'Inicio rápido', link: '/guia-inicio' },
        ],
      },
      {
        text: 'Arquitectura',
        items: [
          { text: 'Visión general', link: '/arquitectura' },
          { text: 'Frontend', link: '/frontend' },
        ],
      },
      {
        text: 'Referencia API',
        items: [
          { text: 'Todos los endpoints', link: '/api' },
        ],
      },
      {
        text: 'Despliegue',
        items: [
          { text: 'Docker Compose', link: '/despliegue' },
        ],
      },
    ],

    footer: {
      message: 'Proyecto académico · Ingeniería de Software · 2026',
      copyright: 'Samuel Zapata · John Eduar Pérez · Juan Esteban Osorno · Juan Camilo Patiño',
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/JohnEduar/reservas-ia' },
    ],

    search: {
      provider: 'local',
    },
  },
})
