import pygame
import math
import sys

# Pygame 초기화
pygame.init()

# 화면 설정
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("포켓몬 카트라이더 (Pokémon Kart)")

# 색상 정의
GREEN = (34, 139, 34)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)  # 피카츄
BLUE = (30, 144, 255)   # 꼬북이
BLACK = (0, 0, 0)

clock = pygame.time.Clock()

class Kart:
    def __init__(self, x, y, color, name):
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.angle = 0
        self.speed = 0
        self.max_speed = 6.5
        self.acceleration = 0.12
        self.friction = 0.04
        self.turn_speed = 3.5
        self.boost_timer = 0

    def update(self, keys=None, is_ai=False):
        if not is_ai and keys:
            # 방향 조향
            if keys[pygame.K_LEFT]:
                self.angle += self.turn_speed * (self.speed / self.max_speed if self.speed != 0 else 1)
            if keys[pygame.K_RIGHT]:
                self.angle -= self.turn_speed * (self.speed / self.max_speed if self.speed != 0 else 1)

            # 가속 및 감속
            if keys[pygame.K_UP]:
                self.speed = min(self.speed + self.acceleration, self.max_speed)
            elif keys[pygame.K_DOWN]:
                self.speed = max(self.speed - self.acceleration, -self.max_speed / 2)
            else:
                if self.speed > 0:
                    self.speed = max(0, self.speed - self.friction)
                elif self.speed < 0:
                    self.speed = min(0, self.speed + self.friction)

            # 피카츄 백만볼트 부스터 (스페이스바)
            if keys[pygame.K_SPACE] and self.boost_timer == 0:
                self.boost_timer = 45  # 부스터 지속 시간 (프레임 단위)
                self.speed = self.max_speed * 1.6

        if self.boost_timer > 0:
            self.boost_timer -= 1

        # 위치 업데이트
        rad = math.radians(self.angle)
        self.x += self.speed * math.cos(rad)
        self.y -= self.speed * math.sin(rad)

    def draw(self, surface):
        rad = math.radians(self.angle)
        size = 14
        
        # 카트 그리기 (삼각형 형태의 차량)
        points = [
            (self.x + math.cos(rad) * size * 1.5, self.y - math.sin(rad) * size * 1.5),
            (self.x + math.cos(rad + 2.4) * size, self.y - math.sin(rad + 2.4) * size),
            (self.x + math.cos(rad - 2.4) * size, self.y - math.sin(rad - 2.4) * size),
        ]

        # 부스터 발동 이펙트
        if self.boost_timer > 0:
            pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), size + 8, 3)

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, BLACK, points, 2)

        # 캐릭터 이름 표시
        font = pygame.font.SysFont("malgungothic", 14)
        text = font.render(self.name, True, BLACK)
        surface.blit(text, (self.x - 18, self.y - 28))

def main():
    player = Kart(400, 520, YELLOW, "피카츄")
    ai_kart = Kart(400, 550, BLUE, "꼬북이")

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys=keys)

        # AI 꼬북이 자동 주행 로직
        ai_kart.angle += 0.8
        ai_kart.speed = 3.5
        ai_kart.update(is_ai=True)

        # 트랙 및 배경 그리기
        screen.fill(GREEN)
        pygame.draw.ellipse(screen, GRAY, (100, 80, 600, 440))       # 외각 도로
        pygame.draw.ellipse(screen, GREEN, (220, 180, 360, 240))     # 중앙 잔디 영역
        pygame.draw.line(screen, WHITE, (400, 480), (400, 580), 4)   # 스타트라인

        # 캐릭터 그리기
        player.draw(screen)
        ai_kart.draw(screen)

        # UI 가이드
        font = pygame.font.SysFont("malgungothic", 18)
        guide = font.render("조작: 방향키 (운전) | Space (백만볼트 부스터)", True, WHITE)
        screen.blit(guide, (20, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
