import os
import shutil
import zipfile
import pandas as pd

import utils

class StatementSpliter(object):
  def __init__(self, app=None):
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    self.__logger = app.logger
    self.__config = app.config

    # 拆分标题
    first_break_down_field = '发票抬头'
    second_break_down_field = '用车原因'
    
    # 公司名字
    entities = [
      '上海虎羽信息技术有限公司',
      '上海布雷克索信息科技有限公司',
      '杭州大搜车汽车服务有限公司上海分公司'
    ]

    # 报表中的sheets
    self.available_sheets = [
        {
            'name': '国内机票对账单',
            'break_col': first_break_down_field,
            'break_val': entities,
        },
        {
            'name': '国内酒店对账单',
            'break_col': first_break_down_field,
            'break_val': entities
        },
        {
            'name': '国内用车对账单',
            'break_col': first_break_down_field,
            'break_val': entities,
            'children': [
                {
                    'name': '出差打车',
                    'filters': ['差旅用车', '市内交通'],
                    'break_col': second_break_down_field,
                    'break_val': entities,
                },
                {
                    'name': '夜间福利打车',
                    'filters': ['加班用车'],
                    'break_col': second_break_down_field,
                    'break_val': entities,
                }
            ]
        },
        {
            'name': '国内商旅火车票对账单',
            'break_col': first_break_down_field,
            'break_val': entities
        },
        {
            'name': '福豆对账单',
            'break_col': first_break_down_field,
            'break_val': entities
        },
    ]
    self.__service_charges = ['国内机票对账单', '国内用车对账单', '国内商旅火车票对账单']
    self.__entities = entities
    spliter = getattr(app, 'spliter', None)

    if not spliter:
      setattr(app, 'spliter', self.__executor)

  def __executor(self, job):
    progress = 0
    storage_path = self.__config.get('UPLOAD_FOLDER')
    job_data = utils.get_job_by_id(job)
    
    file_path = os.path.join(storage_path, job_data.get('filename'))
    self.__logger.info('Spliting account statment ...')
    df_list = []

    per_step_bounce = int(70 / (len(self.available_sheets) + 0.0001))

    file_name = os.path.basename(file_path)
    name, _ = os.path.splitext(file_name)
    file_dir = os.path.dirname(file_path)
    output_zip = os.path.join(file_dir, f'{name}.zip')

    output_path = os.path.join(storage_path, job)
    
    if not os.path.exists(output_path):
      os.mkdir(output_path, mode=0o777)

    for sheet in self.available_sheets:
      sheet_name = sheet.get('name')
      self.__logger.info(f'Processing sheet {sheet_name} ...')

      df = pd.read_excel(file_path, sheet_name=sheet_name, header=2, engine='openpyxl')
      self.__batch_seperator(df, [sheet], output_path)

      job_data['progress'] = progress + per_step_bounce
      utils.save_job(job, job_data)

    for sc in self.__service_charges:
      df = pd.read_excel(file_path, sheet_name=sc, header=2)
      df_list.append(df)

      job_data['progress'] = progress + 10
      utils.save_job(job, job_data)
    
    all_in_one_df = pd.concat(df_list, ignore_index=True)
    self.__split_service_charge(all_in_one_df, output_path=output_path)
    self.__logger.info(f'Starting compress files into {output_zip}.')
    zip = zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED)
    for path, dir, filenames in os.walk(output_path):
      relative = path.replace(output_path, '')
      for _filename in filenames:
        zip.write(os.path.join(path, _filename), os.path.join(relative, _filename))

    zip.close

    # if os.path.exists(file_path):
    #   os.remove(file_path)
    # shutil.rmtree(output_path)

    self.__logger.info('Progress complete!')
    return output_zip

  def __split_service_charge(self, dataframe, output_path):
    first_col = '发票抬头'
    second_col = '服务费'
    
    for entity in self.__entities:
        output_name = f'{entity}_{second_col}'
        entity_df = dataframe[(dataframe[first_col] == entity) & (dataframe[second_col].notna())]
        file_path = os.path.join(output_path, f'{output_name}.xlsx')
        entity_df.to_excel(file_path,
                           sheet_name=f'{"_".join(self.__service_charges)}_{second_col}', columns=['部门', second_col], index=False)

  def __split_to_subs(self, dataframe, file_name, column, values, output_path):
    empty = getattr(dataframe, 'empty', False)
    result_df = pd.DataFrame()

    if not empty:
      result_df = dataframe[dataframe[column].isin(values)]
      file_path = os.path.join(output_path, f'{file_name}.xlsx')
      self.__logger.info(f'Saving sub file to {file_path}')
      result_df.to_excel(file_path, sheet_name=file_name, index=False)

    return result_df

  def __batch_seperator(self, df, sheets, output_path):
    empty = getattr(df, 'empty', False)
    
    if not empty:
      for sheet in sheets:
        sheet_name = sheet.get('name')
        break_col = sheet.get('break_col')
        break_val = sheet.get('break_val')
        children = sheet.get('children')
        self.__logger.info(f'{sheet_name} - {break_col} - {break_val}')

        for val_with_col in break_val:
          values = [val_with_col]
          new_name = f'{val_with_col}_{sheet_name}'

          new_df = self.__split_to_subs(
              df, file_name=new_name, column=break_col, values=values, output_path=output_path)

          if children and len(children):
            for child in children:
              child_name = child.get('name')
              column_name = child.get('break_col')
              filters = child.get('filters')
              self.__split_to_subs(
                  new_df, file_name=f'{new_name}_{child_name}', column=column_name, values=filters, output_path=output_path)
    
