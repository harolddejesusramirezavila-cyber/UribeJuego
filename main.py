import os
import sys
import pygame

# --- FORZAR CARPETA DEL JUEGO ---
directorio_actual = os.path.dirname(os.path.abspath(__file__))
os.chdir(directorio_actual)

# Inicialización
pygame.init()
ANCHO, ALTO = 800, 450
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Uribe Bros - Edición APK")
reloj = pygame.time.Clock()


# --- CARGA SEGURA DE ASSETS ---
def cargar_img(nombre_base, tamano=None, quitar_fondo=True):
    posibles = [
        nombre_base,
        f"{nombre_base}.jpg",
        f"{nombre_base}.jpeg",
        f"{nombre_base}.png",
        f"{nombre_base}.jpg.jpg",
    ]
    for nombre in posibles:
        if os.path.exists(nombre):
            try:
                img = pygame.image.load(nombre).convert()
                if quitar_fondo:
                    img.set_colorkey((255, 255, 255))
                if tamano:
                    img = pygame.transform.scale(img, tamano)
                return img
            except Exception:
                pass
    surf = pygame.Surface(tamano if tamano else (40, 40))
    surf.fill((255, 0, 0))
    return surf


# Assets
img_fondo1 = cargar_img("fondo.jpg", (ANCHO, ALTO), quitar_fondo=False)
img_fondo2 = cargar_img("fondonivel2.jpg", (ANCHO, ALTO), quitar_fondo=False)
img_bloque = cargar_img("bloque.jpg", (40, 40), quitar_fondo=False)
img_magma = cargar_img("magma.jpg", (40, 40), quitar_fondo=False)
img_uribe_original = cargar_img("uribe.jpg", (35, 50))
img_esqueleto = cargar_img("esqueleto.jpg", (40, 45))
img_hechicero = cargar_img("enemigo2.jpg", (45, 55))
img_jefe = cargar_img("jefe.jpg", (100, 120))
img_proyectil = cargar_img("ataque.jpg", (25, 25))
img_dpad = cargar_img("joistick.jpg", (120, 120))
img_acciones = cargar_img("botoestactiles.jpg", (130, 130))


# --- CLASES ---
class Proyectil(pygame.sprite.Sprite):

    def __init__(self, x, y, direccion):
        super().__init__()
        self.image = img_proyectil
        if direccion < 0:
            self.image = pygame.transform.flip(img_proyectil, True, False)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = direccion * 8

    def update(self):
        self.rect.x += self.vel_x
        if self.rect.right < 0 or self.rect.left > ANCHO:
            self.kill()


class Jugador(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.img_base = img_uribe_original
        self.image = self.img_base
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.en_suelo = False
        self.agachado = False
        self.mirando_derecha = True

    def update(self, plataformas):
        self.vel_y += 0.8
        if self.vel_y > 10:
            self.vel_y = 10
        if self.vel_x > 0:
            self.mirando_derecha = True
        elif self.vel_x < 0:
            self.mirando_derecha = False

        base = (
            pygame.transform.scale(img_uribe_original, (35, 30))
            if self.agachado
            else self.img_base
        )
        self.image = (
            pygame.transform.flip(base, True, False)
            if not self.mirando_derecha
            else base
        )

        self.rect.x += self.vel_x
        for p in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel_x > 0:
                self.rect.right = p.rect.left
            elif self.vel_x < 0:
                self.rect.left = p.rect.right

        self.rect.y += self.vel_y
        self.en_suelo = False
        for p in pygame.sprite.spritecollide(self, plataformas, False):
            if self.vel_y > 0:
                self.rect.bottom = p.rect.top
                self.vel_y = 0
                self.en_suelo = True
            elif self.vel_y < 0:
                self.rect.top = p.rect.bottom
                self.vel_y = 0

    def saltar(self):
        if self.en_suelo:
            self.vel_y = -12

    def pegar(self, enemigos):
        alcance = pygame.Rect(
            self.rect.right if self.mirando_derecha else self.rect.left - 40,
            self.rect.y,
            40,
            self.rect.height,
        )
        for e in enemigos:
            if alcance.colliderect(e.rect):
                e.kill()

    def agacharse(self):
        self.agachado = not self.agachado
        pos_y = self.rect.bottom
        self.rect.height = 30 if self.agachado else 50
        self.rect.bottom = pos_y

    def disparar(self, grupo):
        bala = Proyectil(
            self.rect.centerx,
            self.rect.centery,
            1 if self.mirando_derecha else -1,
        )
        grupo.add(bala)


class Bloque(pygame.sprite.Sprite):

    def __init__(self, x, y, es_magma=False):
        super().__init__()
        self.image = img_magma if es_magma else img_bloque
        self.rect = self.image.get_rect(topleft=(x, y))


class Esqueleto(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.image = img_esqueleto
        self.rect = self.image.get_rect(topleft=(x, y))
        self.dir = 1
        self.pasos = 0

    def update(self):
        self.rect.x += self.dir * 2
        self.pasos += 1
        if self.pasos > 40:
            self.dir *= -1
            self.pasos = 0


class Hechicero(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.image = img_hechicero
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = 0

    def update(self, proyectiles_enemigos, x_jugador):
        self.timer += 1
        if self.timer >= 60:  # Dispara cada segundo
            self.timer = 0
            dir_x = -1 if x_jugador < self.rect.x else 1
            proyectil = Proyectil(self.rect.centerx, self.rect.centery, dir_x)
            proyectiles_enemigos.add(proyectil)


class Jefe(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.image = img_jefe
        self.rect = self.image.get_rect(topleft=(x, y))
        self.dir = -1
        self.pasos = 0

    def update(self):
        self.rect.x += self.dir * 2
        self.pasos += 1
        if self.pasos > 50:
            self.dir *= -1
            self.pasos = 0


# --- MAPAS ---
mapa_nivel_1 = [
    "                                        ",
    "                                        ",
    "         E                              ",
    "      XXXXXX                            ",
    "                                 XXXXX  ",
    "  XXXX                                  ",
    "                                        ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

mapa_nivel_2 = [
    "                                        ",
    "                                    J   ",
    "                                 XXXXXXX",
    "            H                           ",
    "         XXXXXX                         ",
    "  H                 XXXXX               ",
    "XXXXX                                   ",
    "        XXXXXX            XXXXX         ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]


def cargar_nivel(mapa, es_nivel2=False):
    plataformas, enemigos, todos = (
        pygame.sprite.Group(),
        pygame.sprite.Group(),
        pygame.sprite.Group(),
    )
    jugador = Jugador(50, 200)
    todos.add(jugador)

    for f, fila in enumerate(mapa):
        for c, col in enumerate(fila):
            x, y = c * 40, f * 40
            if col == "X":
                b = Bloque(x, y, es_magma=es_nivel2)
                plataformas.add(b)
                todos.add(b)
            elif col == "E":
                e = Esqueleto(x, y)
                enemigos.add(e)
                todos.add(e)
            elif col == "H":
                h = Hechicero(x, y - 15)
                enemigos.add(h)
                todos.add(h)
            elif col == "J":
                j = Jefe(x - 40, y - 80)
                enemigos.add(j)
                todos.add(j)

    return jugador, plataformas, enemigos, todos


# --- CONTROLES Y BUCLE PRINCIPAL ---
btn_izq = pygame.Rect(5, 340, 40, 50)
btn_der = pygame.Rect(80, 340, 40, 50)
btn_A = pygame.Rect(700, 370, 50, 50)
btn_B = pygame.Rect(740, 310, 50, 50)
btn_X = pygame.Rect(660, 310, 50, 50)
btn_Y = pygame.Rect(700, 260, 50, 50)

jugador, plataformas, enemigos, todos = cargar_nivel(mapa_nivel_1)
proyectiles_jugador = pygame.sprite.Group()
proyectiles_enemigos = pygame.sprite.Group()
nivel_actual = 1
ejecutando = True

while ejecutando:
    reloj.tick(60)
    jugador.vel_x = 0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            ejecutando = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if btn_A.collidepoint(e.pos):
                jugador.saltar()
            if btn_B.collidepoint(e.pos):
                jugador.pegar(enemigos)
            if btn_X.collidepoint(e.pos):
                jugador.agacharse()
            if btn_Y.collidepoint(e.pos):
                jugador.disparar(proyectiles_jugador)

    if pygame.mouse.get_pressed()[0]:
        pos = pygame.mouse.get_pos()
        if btn_izq.collidepoint(pos):
            jugador.vel_x = -5
        elif btn_der.collidepoint(pos):
            jugador.vel_x = 5

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        jugador.vel_x = -5
    if keys[pygame.K_RIGHT]:
        jugador.vel_x = 5
    if keys[pygame.K_SPACE]:
        jugador.saltar()

    # Actualizaciones de Sprites
    jugador.update(plataformas)
    proyectiles_jugador.update()
    proyectiles_enemigos.update()

    # Actualización específica de Inteligencia de Enemigos
    for e in enemigos:
        if isinstance(e, (Esqueleto, Jefe)):
            e.update()
        elif isinstance(e, Hechicero):
            e.update(proyectiles_enemigos, jugador.rect.x)

    # Colisiones
    pygame.sprite.groupcollide(
        proyectiles_jugador, enemigos, True, True
    )  # Tus disparos destruyen enemigos
    pygame.sprite.spritecollide(
        jugador, proyectiles_enemigos, True
    )  # Los disparos enemigos te impactan

    # Transición Nivel 1 -> Nivel 2
    if nivel_actual == 1 and jugador.rect.x > 760:
        nivel_actual = 2
        proyectiles_enemigos.empty()
        proyectiles_jugador.empty()
        jugador, plataformas, enemigos, todos = cargar_nivel(
            mapa_nivel_2, es_nivel2=True
        )

    # Renderizado
    pantalla.blit(img_fondo1 if nivel_actual == 1 else img_fondo2, (0, 0))
    todos.draw(pantalla)
    proyectiles_jugador.draw(pantalla)
    proyectiles_enemigos.draw(pantalla)

    pantalla.blit(img_dpad, (5, 305))
    pantalla.blit(img_acciones, (650, 250))

    pygame.display.flip()

pygame.quit()
sys.exit()