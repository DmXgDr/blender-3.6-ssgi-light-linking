/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 */

#include <cstdio>
#include <memory>

#include "BLI_listbase.h"

#include "BLT_translation.h"

#include "DNA_collection_types.h"
#include "DNA_object_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_context.h"
#include "BKE_light_linking.h"

#include "RNA_access.h"
#include "RNA_prototypes.h"

#include "UI_interface.h"
#include "UI_interface.hh"
#include "UI_resources.h"
#include "UI_tree_view.hh"
#include "interface_intern.hh"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_undo.h"

using blender::StringRefNull;

namespace blender::ui::light_linking {

namespace {

class CollectionDropTarget {
  Collection &collection_;

 public:
  bool can_drop(const wmDrag &drag, const char **r_disabled_hint) const
  {
    if (drag.type != WM_DRAG_ID) {
      return false;
    }

    const wmDragID *drag_id = static_cast<wmDragID *>(drag.ids.first);
    if (!drag_id) {
      return false;
    }

    /* The dragged IDs are guaranteed to be the same type, so only check the type of the first one.
     */
    const ID_Type id_type = GS(drag_id->id->name);
    if (!ELEM(id_type, ID_OB, ID_GR)) {
      *r_disabled_hint = "Can only add objects and collections to the light linking collection";
      return false;
    }

    return true;
  }

  CollectionDropTarget(Collection &collection) : collection_(collection) {}

  Collection &get_collection() const
  {
    return collection_;
  }
};

/**
 * Drop target for the view (when dropping into empty space of the view), not for an item.
 */
class InsertCollectionDropTarget : public AbstractViewItemDropTarget {
  CollectionDropTarget target_;
  const ID *before_;

 public:
  InsertCollectionDropTarget(AbstractView &view,
                             Collection &collection,
                             const ID *before = nullptr)
      : AbstractViewItemDropTarget(view),
        target_(collection),
        before_(before)
  {
  }
  bool can_drop(const wmDrag &drag, const char **hint) const override
  {
    return target_.can_drop(drag, hint);
  }
  std::string drop_tooltip(const wmDrag &) const override
  {
    return before_ ? TIP_("Insert above or below this linking item") :
                     TIP_("Add to linking collection");
  }
  bool on_drop(bContext *C, const wmDrag &drag) const override
  {
    return on_drop_event(C, drag, *CTX_wm_window(C)->eventstate);
  }
  bool on_drop_event(bContext *C, const wmDrag &drag, const wmEvent &event) const override
  {
    Main *bmain = CTX_data_main(C);
    bool insert_after = false;
    /* In 3.6 an active row button may be reused from the previous UI block.
     * Query the actual hit-tested button, whose rectangle matches the displayed row. */
    uiBut *item_button = before_ ? ui_view_item_find_mouse_over(CTX_wm_region(C), event.xy) :
                                  nullptr;
    if (item_button) {
      float x = float(event.xy[0]);
      float y = float(event.xy[1]);
      ui_window_to_block_fl(CTX_wm_region(C), item_button->block, &x, &y);
      insert_after = y < BLI_rctf_cent_y(&item_button->rect);
    }
    const ID *anchor = before_;
    LISTBASE_FOREACH (wmDragID *, item, &drag.ids) {
      if (item->id == before_) {
        continue;
      }
      if (insert_after) {
        BKE_light_linking_add_receiver_to_collection_after(bmain,
                                                           &target_.get_collection(),
                                                           item->id,
                                                           anchor,
                                                           COLLECTION_LIGHT_LINKING_STATE_INCLUDE);
        anchor = item->id;
      }
      else if (before_) {
        BKE_light_linking_add_receiver_to_collection_before(
            bmain,
            &target_.get_collection(),
            item->id,
            before_,
            COLLECTION_LIGHT_LINKING_STATE_INCLUDE);
      }
      else {
        BKE_light_linking_add_receiver_to_collection(
            bmain, &target_.get_collection(), item->id, COLLECTION_LIGHT_LINKING_STATE_INCLUDE);
      }
    }
    WM_event_add_notifier(C, NC_SCENE | ND_LAYER_CONTENT, CTX_data_scene(C));
    ED_undo_push(C, "Add to linking collection");
    return true;
  }
};

class ItemDragController : public AbstractViewItemDragController {
  ID &id_;

 public:
  explicit ItemDragController(AbstractView &view, ID &id)
      : AbstractViewItemDragController(view), id_(id)
  {
  }

  int get_drag_type() const override
  {
    return WM_DRAG_ID;
  }

  void *create_drag_data() const override
  {
    return static_cast<void *>(&id_);
  }
};

class CollectionViewItem : public BasicTreeViewItem {
  uiLayout &context_layout_;
  Collection &collection_;

  ID &id_;
  CollectionLightLinking &collection_light_linking_;

 public:
  CollectionViewItem(uiLayout &context_layout,
                     Collection &collection,
                     ID &id,
                     CollectionLightLinking &collection_light_linking,
                     const BIFIconID icon)
      : BasicTreeViewItem(id.name + 2, icon),
        context_layout_(context_layout),
        collection_(collection),
        id_(id),
        collection_light_linking_(collection_light_linking)
  {
  }

  void build_row(uiLayout &row) override
  {
    if (is_active()) {
      PointerRNA id_ptr;
      RNA_id_pointer_create(&id_, &id_ptr);
      PointerRNA collection_ptr;
      RNA_id_pointer_create(&collection_.id, &collection_ptr);

      uiLayoutSetContextPointer(&context_layout_, "id", &id_ptr);
      uiLayoutSetContextPointer(&context_layout_, "collection", &collection_ptr);
    }

    /* Data-block names are user content. BasicTreeViewItem translates UI labels,
     * which would turn names such as "Suzanne" into a different displayed name. */
    uiItemL(&row, id_.name + 2, icon);

    uiLayout *sub = uiLayoutRow(&row, true);
    uiLayoutSetPropDecorate(sub, false);

    build_state_button(*sub);
  }

  std::unique_ptr<AbstractViewItemDragController> create_drag_controller() const override
  {
    return std::make_unique<ItemDragController>(get_tree_view(), id_);
  }

  std::unique_ptr<AbstractViewItemDropTarget> create_drop_target() override
  {
    return std::make_unique<InsertCollectionDropTarget>(
        get_tree_view(), collection_, &id_);
  }

 private:
  int get_state_icon() const
  {
    switch (collection_light_linking_.link_state) {
      case COLLECTION_LIGHT_LINKING_STATE_INCLUDE:
        return ICON_CHECKBOX_HLT;
      case COLLECTION_LIGHT_LINKING_STATE_EXCLUDE:
        return ICON_CHECKBOX_DEHLT;
    }
    BLI_assert_unreachable();
    return ICON_NONE;
  }

  static void link_state_toggle(CollectionLightLinking &collection_light_linking)
  {
    switch (collection_light_linking.link_state) {
      case COLLECTION_LIGHT_LINKING_STATE_INCLUDE:
        collection_light_linking.link_state = COLLECTION_LIGHT_LINKING_STATE_EXCLUDE;
        return;
      case COLLECTION_LIGHT_LINKING_STATE_EXCLUDE:
        collection_light_linking.link_state = COLLECTION_LIGHT_LINKING_STATE_INCLUDE;
        return;
    }

    BLI_assert_unreachable();
  }

  void build_state_button(uiLayout &row)
  {
    uiBlock *block = uiLayoutGetBlock(&row);
    const int icon = get_state_icon();

    PointerRNA collection_light_linking_ptr;
    RNA_pointer_create(&collection_.id,
                       &RNA_CollectionLightLinking,
                       &collection_light_linking_,
                       &collection_light_linking_ptr);

    uiBut *button = uiDefIconButR(block,
                                  UI_BTYPE_BUT,
                                  0,
                                  icon,
                                  0,
                                  0,
                                  UI_UNIT_X,
                                  UI_UNIT_Y,
                                  &collection_light_linking_ptr,
                                  "link_state",
                                  0,
                                  0.0f,
                                  0.0f,
                                  0.0f,
                                  0.0f,
                                  nullptr);

    /* 3.6 does not enable undo by default for UI_BTYPE_BUT, even with RNA data. */
    UI_but_flag_enable(button, UI_BUT_UNDO);
    UI_but_func_set(
        button,
        [](bContext *C, void *collection, void *settings) {
          link_state_toggle(*static_cast<CollectionLightLinking *>(settings));
          PointerRNA ptr;
          RNA_pointer_create(&static_cast<Collection *>(collection)->id,
                             &RNA_CollectionLightLinking,
                             settings,
                             &ptr);
          RNA_property_update(C, &ptr, RNA_struct_find_property(&ptr, "link_state"));
        },
        &collection_,
        &collection_light_linking_);
  }
};

class CollectionView : public AbstractTreeView {
  uiLayout &context_layout_;
  Collection &collection_;

 public:
  CollectionView(uiLayout &context_layout, Collection &collection)
      : context_layout_(context_layout), collection_(collection)
  {
  }

  void build_tree() override
  {
    LISTBASE_FOREACH (CollectionChild *, collection_child, &collection_.children) {
      Collection *child_collection = collection_child->collection;
      add_tree_item<CollectionViewItem>(context_layout_,
                                        collection_,
                                        child_collection->id,
                                        collection_child->light_linking,
                                        ICON_OUTLINER_COLLECTION);
    }

    LISTBASE_FOREACH (CollectionObject *, collection_object, &collection_.gobject) {
      Object *child_object = collection_object->ob;
      add_tree_item<CollectionViewItem>(context_layout_,
                                        collection_,
                                        child_object->id,
                                        collection_object->light_linking,
                                        ICON_OBJECT_DATA);
    }
  }

  std::unique_ptr<AbstractViewDropTarget> create_drop_target() override
  {
    return std::make_unique<InsertCollectionDropTarget>(*this, collection_);
  }
};

}  // namespace

}  // namespace blender::ui::light_linking

void uiTemplateLightLinkingCollection(
    uiLayout *layout, bContext *C, uiLayout *context_layout, PointerRNA *ptr, const char *propname)
{
  if (!ptr->data) {
    return;
  }

  PropertyRNA *prop = RNA_struct_find_property(ptr, propname);
  if (!prop) {
    printf(
        "%s: property not found: %s.%s\n", __func__, RNA_struct_identifier(ptr->type), propname);
    return;
  }

  if (RNA_property_type(prop) != PROP_POINTER) {
    printf("%s: expected pointer property for %s.%s\n",
           __func__,
           RNA_struct_identifier(ptr->type),
           propname);
    return;
  }

  const PointerRNA collection_ptr = RNA_property_pointer_get(ptr, prop);
  if (!collection_ptr.data) {
    return;
  }
  if (collection_ptr.type != &RNA_Collection) {
    printf("%s: expected collection pointer property for %s.%s\n",
           __func__,
           RNA_struct_identifier(ptr->type),
           propname);
    return;
  }

  Collection *collection = static_cast<Collection *>(collection_ptr.data);

  uiBlock *block = uiLayoutGetBlock(layout);

  blender::ui::AbstractTreeView *tree_view = UI_block_add_view(
      *block,
      "Light Linking Collection Tree View",
      std::make_unique<blender::ui::light_linking::CollectionView>(*context_layout, *collection));
  tree_view->set_min_rows(5);

  blender::ui::TreeViewBuilder::build_tree_view(*tree_view, *layout);
}
