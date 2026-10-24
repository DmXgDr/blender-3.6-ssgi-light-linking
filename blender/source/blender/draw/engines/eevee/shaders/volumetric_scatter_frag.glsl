
#pragma BLENDER_REQUIRE(volumetric_lib.glsl)

/* Based on Frosbite Unified Volumetric.
 * https://www.ea.com/frostbite/news/physically-based-unified-volumetric-rendering-in-frostbite */

/* Step 2 : Evaluate all light scattering for each froxels.
 * Also do the temporal reprojection to fight aliasing artifacts. */

void main()
{
  ivec3 volume_cell = ivec3(ivec2(gl_FragCoord.xy), volumetric_geom_iface.slice);

  /* Emission */
#ifdef VOLUME_LINKING_ACCUMULATE
  /* Only direct light is additive. Extinction, emission, environment and history
   * are resolved once, after all independently linked media have contributed. */
  outScattering = vec4(0.0);
  outTransmittance = vec4(0.0);
#else
  outScattering = texelFetch(volumeEmission, volume_cell, 0);
  outTransmittance = texelFetch(volumeExtinction, volume_cell, 0);
#endif
  vec3 s_scattering = texelFetch(volumeScattering, volume_cell, 0).rgb;
  vec3 volume_ndc = volume_to_ndc((vec3(volume_cell) + volJitter.xyz) * volInvTexSize.xyz);
  vec3 P = get_world_space_from_depth(volume_ndc.xy, volume_ndc.z);
  vec3 V = cameraVec(P);

  vec2 phase = texelFetch(volumePhase, volume_cell, 0).rg;
  float s_anisotropy = phase.x / max(1.0, phase.y);

  /* Environment : Average color. */
#ifndef VOLUME_LINKING_ACCUMULATE
  outScattering.rgb += irradiance_volumetric(P) * s_scattering * phase_function_isotropic();
#endif

#ifdef VOLUME_LIGHTING /* Lights */
#  ifndef VOLUME_LINKING_ACCUMULATE
  if (volumeUseLinkedScattering) {
    outScattering.rgb += texelFetch(volumeLinkedScattering, volume_cell, 0).rgb;
  }
  else
#  endif
  {
    for (int i = 0; i < MAX_LIGHT && i < laNumLight; i++) {
      LightData ld = lights_data[i];

      if (ld.l_volume == 0.0) {
        continue;
      }
      if (volumeReceiverSet >= 0) {
        uint receiver_set = uint(volumeReceiverSet);
        if ((ld.light_linking_mask[receiver_set >> 5u] & (1u << (receiver_set & 31u))) == 0u) {
          continue;
        }
      }

      vec4 l_vector;
      l_vector.xyz = light_volume_light_vector(ld, P);
      l_vector.w = length(l_vector.xyz);

      float vis = light_visibility(ld, P, l_vector);

      if (vis < 1e-4) {
        continue;
      }

      vec3 Li = light_volume(ld, l_vector) *
                light_volume_shadow(ld, P, l_vector, volumeExtinction);

      outScattering.rgb += Li * vis * s_scattering *
                           phase_function(-V, l_vector.xyz / l_vector.w, s_anisotropy);
    }
  }
#endif

#ifndef VOLUME_LINKING_ACCUMULATE
  /* Temporal supersampling */
  /* Note : this uses the cell non-jittered position (texel center). */
  vec3 curr_ndc = volume_to_ndc(vec3(gl_FragCoord.xy, float(volumetric_geom_iface.slice) + 0.5) *
                                volInvTexSize.xyz);
  vec3 wpos = get_world_space_from_depth(curr_ndc.xy, curr_ndc.z);
  vec3 prev_ndc = project_point(pastViewProjectionMatrix, wpos);
  vec3 prev_volume = ndc_to_volume(prev_ndc * 0.5 + 0.5);

  if ((volHistoryAlpha > 0.0) && all(greaterThan(prev_volume, vec3(0.0))) &&
      all(lessThan(prev_volume, vec3(1.0))))
  {
    vec4 h_Scattering = texture(historyScattering, prev_volume);
    vec4 h_Transmittance = texture(historyTransmittance, prev_volume);
    outScattering = mix(outScattering, h_Scattering, volHistoryAlpha);
    outTransmittance = mix(outTransmittance, h_Transmittance, volHistoryAlpha);
  }
#endif

  /* Catch NaNs */
  if (any(isnan(outScattering)) || any(isnan(outTransmittance))) {
    outScattering = vec4(0.0);
    outTransmittance = vec4(1.0);
  }
}
