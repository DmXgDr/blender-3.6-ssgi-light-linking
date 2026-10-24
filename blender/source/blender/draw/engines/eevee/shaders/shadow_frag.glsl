
#pragma BLENDER_REQUIRE(common_view_lib.glsl)

void main()
{
  if (shadowLinkingMask.z != 0) {
    uint blocker_set = (uint(ObjectInfo.y) >> 6u) & 63u;
    uint blocker_mask = uint(shadowLinkingMask[blocker_set >> 5u]);
    if ((blocker_mask & (1u << (blocker_set & 31u))) == 0u) {
      discard;
    }
  }
}
