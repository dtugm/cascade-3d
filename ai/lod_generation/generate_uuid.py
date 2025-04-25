from uuid import uuid4
import fiona
from tqdm.autonotebook import tqdm


def generate_uuid(
    input_file: str,
    output_file: str = None,
    fieldname: str = "uuid",
    driver: str = None,
    id_type: str = "uuid",
    overwrite: bool = False,
) -> None:
    with fiona.Env(), fiona.open(input_file) as src:
        out_schema = src.schema.copy()
        if fieldname not in src.schema["properties"].keys():
            out_schema["properties"][fieldname] = "str:32"
        output_file = input_file if output_file is None else output_file
        driver = src.driver if driver is None else driver
        crs = src.crs
        out_dicts = [src_dict for src_dict in src]

    with fiona.open(
        output_file,
        "w",
        driver=driver,
        schema=out_schema,
        crs=crs,
    ) as out:
        for i, out_dict in enumerate(tqdm(out_dicts, "Generating UUID")):
            if fieldname not in out_dict["properties"].keys():
                out_dict["properties"][fieldname] = (
                    uuid4().hex if id_type == "uuid" else i
                )
            else:
                if overwrite:
                    out_dict["properties"][fieldname] = (
                        uuid4().hex if id_type == "uuid" else i
                    )
                elif (
                    len(out_dict["properties"][fieldname]) == 0
                    or out_dict["properties"][fieldname] is None
                ):
                    out_dict["properties"][fieldname] = (
                        uuid4().hex if id_type == "uuid" else i
                    )
            out.write(out_dict)
