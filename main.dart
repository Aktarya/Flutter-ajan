import 'package:flutter/material.dart';
import 'dart:async';
import 'package:intl/intl.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Digital Clock',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: Colors.black,
        textTheme: const TextTheme(
          displayLarge: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          displayMedium: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          displaySmall: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          headlineLarge: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          headlineMedium: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          headlineSmall: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          titleLarge: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          titleMedium: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          titleSmall: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          bodyLarge: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          bodyMedium: TextStyle(color: Colors.white, fontFamily: 'monospace'),
          bodySmall: TextStyle(color: Colors.white, fontFamily: 'monospace'),
        ),
      ),
      home: const DigitalClockApp(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class DigitalClockApp extends StatefulWidget {
  const DigitalClockApp({super.key});

  @override
  State<DigitalClockApp> createState() => _DigitalClockAppState();
}

class _DigitalClockAppState extends State<DigitalClockApp> {
  DateTime _currentTime = DateTime.now();
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    // Ensure 'intl' package is added to pubspec.yaml for DateFormat
    // We'll update every second
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _currentTime = DateTime.now();
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final String formattedTime = DateFormat('HH:mm').format(_currentTime);

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              formattedTime,
              style: const TextStyle(
                fontSize: 96,
                fontWeight: FontWeight.bold,
                color: Colors.lightGreenAccent, // A contrasting color for the time
                shadows: [
                  Shadow(
                    blurRadius: 10.0,
                    color: Colors.black45,
                    offset: Offset(5.0, 5.0),
                  ),
                ],
              ),
            ),
            // Optional: Add seconds in smaller font if needed
            // Text(
            //   DateFormat(':ss').format(_currentTime),
            //   style: const TextStyle(
            //     fontSize: 48,
            //     color: Colors.lightGreenAccent,
            //   ),
            // ),
          ],
        ),
      ),
    );
  }
}