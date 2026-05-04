import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

// --- SteampunkClockApp Widget ---
class SteampunkClockApp extends StatefulWidget {
  const SteampunkClockApp({Key? key}) : super(key: key);

  @override
  State<SteampunkClockApp> createState() => _SteampunkClockAppState();
}

class _SteampunkClockAppState extends State<SteampunkClockApp> with TickerProviderStateMixin {
  DateTime _currentTime = DateTime.now();
  late Timer _timer;

  // Animation controllers for gears
  late AnimationController _gearAnimationController1;
  late AnimationController _gearAnimationController2;
  late AnimationController _gearAnimationController3;

  @override
  void initState() {
    super.initState();
    _updateTime();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _updateTime();
    });

    // Initialize gear animation controllers with different speeds and directions
    _gearAnimationController1 = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10), // Slower rotation
    )..repeat();

    _gearAnimationController2 = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 15), // Even slower rotation, opposite direction
    )..repeat();

    _gearAnimationController3 = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 7), // Faster rotation
    )..repeat();
  }

  void _updateTime() {
    setState(() {
      _currentTime = DateTime.now();
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    _gearAnimationController1.dispose();
    _gearAnimationController2.dispose();
    _gearAnimationController3.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF4B3621), // Koyu Kahverengi
              Color(0xFFA0522D), // Siena / Paslı Bakır
              Color(0xFF8B4513), // Sele Kahverengisi
            ],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: Center(
          child: AspectRatio(
            aspectRatio: 1.0, // Saatin kare bir alanda olmasını sağlar
            child: Stack(
              children: [
                // Arka plan dişlileri - animasyonlu
                Positioned(
                  left: -50,
                  top: -50,
                  child: AnimatedBuilder(
                    animation: _gearAnimationController1,
                    builder: (context, child) {
                      return Transform.rotate(
                        angle: _gearAnimationController1.value * 2 * pi, // Saat yönünde dönme
                        child: CustomPaint(
                          size: const Size(200, 200),
                          painter: GearPainter(
                            toothCount: 15,
                            centerColor: const Color(0xFF6B4226), // Daha koyu kahverengi
                            gearColor: const Color(0xFF8B4513), // Sele kahverengisi
                            borderColor: const Color(0xFFA0522D), // Siena
                            toothLengthRatio: 0.1,
                            innerHoleRatio: 0.4,
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Positioned(
                  right: -70,
                  bottom: -70,
                  child: AnimatedBuilder(
                    animation: _gearAnimationController2,
                    builder: (context, child) {
                      return Transform.rotate(
                        angle: -_gearAnimationController2.value * 2 * pi, // Ters saat yönünde dönme
                        child: CustomPaint(
                          size: const Size(250, 250),
                          painter: GearPainter(
                            toothCount: 20,
                            centerColor: const Color(0xFF8B4513),
                            gearColor: const Color(0xFFA0522D),
                            borderColor: const Color(0xFF6B4226),
                            toothLengthRatio: 0.12,
                            innerHoleRatio: 0.3,
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Positioned(
                  left: 30,
                  bottom: 10,
                  child: AnimatedBuilder(
                    animation: _gearAnimationController3,
                    builder: (context, child) {
                      return Transform.rotate(
                        angle: _gearAnimationController3.value * 2 * pi, // Saat yönünde dönme
                        child: CustomPaint(
                          size: const Size(100, 100),
                          painter: GearPainter(
                            toothCount: 10,
                            centerColor: const Color(0xFFA0522D),
                            gearColor: const Color(0xFF6B4226),
                            borderColor: const Color(0xFF8B4513),
                            toothLengthRatio: 0.15,
                            innerHoleRatio: 0.5,
                          ),
                        ),
                      );
                    },
                  ),
                ),
                // Saat kadranı ve ibreler
                CustomPaint(
                  size: Size.infinite,
                  painter: ClockPainter(_currentTime),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// --- ClockPainter (kadran ve ibreler için) ---
class ClockPainter extends CustomPainter {
  final DateTime currentTime;

  ClockPainter(this.currentTime);

  @override
  void paint(Canvas canvas, Size size) {
    final double centerX = size.width / 2;
    final double centerY = size.height / 2;
    final Offset center = Offset(centerX, centerY);
    final double radius = min(centerX, centerY) * 0.8; // Ana saat kadranı yarıçapı

    // Saat Kadranı Arka Planı
    final Paint dialPaint = Paint()..color = const Color(0xFF2C2C2C); // Koyu gri metalik
    canvas.drawCircle(center, radius, dialPaint);

    // Saat Kadranı Kenarlığı
    final Paint borderPaint = Paint()
      ..color = const Color(0xFFB8860B) // Koyu altın/pirinç
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8.0;
    canvas.drawCircle(center, radius, borderPaint);

    // Saat ve Dakika İşaretleri (tıklar)
    final Paint tickPaint = Paint()
      ..color = const Color(0xFFDAA520) // Goldenrod
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round;

    final Paint hourTickPaint = Paint()
      ..color = const Color(0xFFDAA520) // Goldenrod
      ..strokeWidth = 5.0
      ..strokeCap = StrokeCap.round;

    for (int i = 0; i < 60; i++) {
      final double angle = i * 6 * pi / 180; // Her dakika/saniye için 6 derece
      final double x1 = centerX + radius * cos(angle);
      final double y1 = centerY + radius * sin(angle);

      double x2, y2;
      if (i % 5 == 0) { // Saat işaretleri
        x2 = centerX + (radius - 20) * cos(angle);
        y2 = centerY + (radius - 20) * sin(angle);
        canvas.drawLine(Offset(x1, y1), Offset(x2, y2), hourTickPaint);
      } else { // Dakika işaretleri
        x2 = centerX + (radius - 10) * cos(angle);
        y2 = centerY + (radius - 10) * sin(angle);
        canvas.drawLine(Offset(x1, y1), Offset(x2, y2), tickPaint);
      }
    }

    // İbreler
    // Akrep (Saat ibresi)
    final double hourAngle = (currentTime.hour % 12 + currentTime.minute / 60) * 30 * pi / 180 - pi / 2;
    _drawHand(canvas, center, radius * 0.4, hourAngle, 10.0, const Color(0xFFDAA520)); // Goldenrod

    // Yelkovan (Dakika ibresi)
    final double minuteAngle = (currentTime.minute + currentTime.second / 60) * 6 * pi / 180 - pi / 2;
    _drawHand(canvas, center, radius * 0.6, minuteAngle, 7.0, const Color(0xFFDAA520)); // Goldenrod

    // Saniye ibresi
    final double secondAngle = currentTime.second * 6 * pi / 180 - pi / 2;
    _drawHand(canvas, center, radius * 0.7, secondAngle, 3.0, const Color(0xFFB22222)); // Kırmızı (Firebrick)

    // Saatin merkez noktası
    final Paint centerDotPaint = Paint()..color = const Color(0xFFD4AF37); // Altın
    canvas.drawCircle(center, 8.0, centerDotPaint);
  }

  // İbre çizimi için yardımcı metod
  void _drawHand(Canvas canvas, Offset center, double length, double angle, double baseWidth, Color color) {
    final Paint handPaint = Paint()
      ..color = color
      ..strokeWidth = baseWidth // ibrenin kalınlığı
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.fill; // Kalın bir görünüm için doldurma stilinde

    final Path path = Path();
    final double tipX = center.dx + length * cos(angle);
    final double tipY = center.dy + length * sin(angle);

    // İbrenin taban noktaları
    final double baseAngleOffset = pi / 2; // İbre yönüne dik açıyı almak için
    final double p1X = center.dx + (baseWidth / 2) * cos(angle - baseAngleOffset);
    final double p1Y = center.dy + (baseWidth / 2) * sin(angle - baseAngleOffset);
    final double p2X = center.dx + (baseWidth / 2) * cos(angle + baseAngleOffset);
    final double p2Y = center.dy + (baseWidth / 2) * sin(angle + baseAngleOffset);

    // İbreyi bir üçgen olarak çiz
    path.moveTo(tipX, tipY);
    path.lineTo(p1X, p1Y);
    path.lineTo(p2X, p2Y);
    path.close();

    canvas.drawPath(path, handPaint);
  }

  @override
  bool shouldRepaint(covariant ClockPainter oldDelegate) {
    return oldDelegate.currentTime != currentTime;
  }
}

// --- GearPainter (dişli çarkları çizmek için) ---
class GearPainter extends CustomPainter {
  final int toothCount; // Diş sayısı
  final Color gearColor; // Dişli çarkın rengi
  final Color borderColor; // Kenar rengi
  final Color centerColor; // Merkez rengi
  final double toothLengthRatio; // Dişlerin ana yarıçapın ne kadar dışına çıktığı oranı
  final double innerHoleRatio; // İç delik yarıçapının ana yarıçapa oranı

  GearPainter({
    required this.toothCount,
    required this.gearColor,
    required this.borderColor,
    required this.centerColor,
    this.toothLengthRatio = 0.1,
    this.innerHoleRatio = 0.3,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final double centerX = size.width / 2;
    final double centerY = size.height / 2;
    final Offset center = Offset(centerX, centerY);
    final double radius = min(centerX, centerY);
    final double outerRadius = radius;
    final double innerToothRadius = outerRadius * (1 - toothLengthRatio); // Dişlerin başladığı yarıçap
    final double innerHoleRadius = outerRadius * innerHoleRatio; // Merkezi deliğin yarıçapı

    final Paint gearBodyPaint = Paint()..color = gearColor;
    final Paint borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    final Paint centerPaint = Paint()..color = centerColor;

    // Ana dişli gövdesini çiz
    canvas.drawCircle(center, innerToothRadius, gearBodyPaint);

    // Dişleri çiz
    final double angleStep = 2 * pi / toothCount; // Her bir diş arasındaki açı
    final double toothWidthAngle = angleStep * 0.4; // Her dişin genişliği

    for (int i = 0; i < toothCount; i++) {
      final double startAngle = i * angleStep;
      final double endAngle = startAngle + toothWidthAngle;

      final Path toothPath = Path();
      toothPath.moveTo(centerX + innerToothRadius * cos(startAngle),
                       centerY + innerToothRadius * sin(startAngle));
      toothPath.lineTo(centerX + outerRadius * cos(startAngle),
                       centerY + outerRadius * sin(startAngle));
      toothPath.lineTo(centerX + outerRadius * cos(endAngle),
                       centerY + outerRadius * sin(endAngle));
      toothPath.lineTo(centerX + innerToothRadius * cos(endAngle),
                       centerY + innerToothRadius * sin(endAngle));
      toothPath.close();

      canvas.drawPath(toothPath, gearBodyPaint);
      canvas.drawPath(toothPath, borderPaint); // Her diş için kenarlık çiz
    }

    // İç deliği çiz
    canvas.drawCircle(center, innerHoleRadius, gearBodyPaint);
    canvas.drawCircle(center, innerHoleRadius, borderPaint);

    // Merkez pimi/cıvatayı çiz
    canvas.drawCircle(center, innerHoleRadius * 0.5, centerPaint);
    canvas.drawCircle(center, innerHoleRadius * 0.5, borderPaint);
  }

  @override
  bool shouldRepaint(covariant GearPainter oldDelegate) {
    return toothCount != oldDelegate.toothCount ||
           gearColor != oldDelegate.gearColor ||
           borderColor != oldDelegate.borderColor ||
           centerColor != oldDelegate.centerColor ||
           toothLengthRatio != oldDelegate.toothLengthRatio ||
           innerHoleRatio != oldDelegate.innerHoleRatio;
  }
}

// --- Ana uygulama giriş noktası ---
void main() {
  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false, // Debug bandını kaldır
    home: SteampunkClockApp(),
  ));
}