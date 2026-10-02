import 'dart:convert';
import 'package:flutter/services.dart';
import 'models/journey_stage.dart';

class JourneyRepository {
  Future<List<JourneyStage>> loadIndonesiaManufacturing2026() async {
    const path = 'assets/packs/id_e9_manufacturing_2026.json';
    final raw = await rootBundle.loadString(path);
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final stages = data['stages'] as List<dynamic>;
    return stages
        .map((e) => JourneyStage.fromJson(e as Map<String, dynamic>))
        .toList(growable: false);
  }
}
